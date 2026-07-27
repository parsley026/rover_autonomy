"""
aruco_localization_node.py
==========================
ROS 2 node that converts ArUco marker detections into absolute map-frame
pose corrections and feeds them into the robot_localization EKF via
geometry_msgs/PoseWithCovarianceStamped.

Strategy: Multi-Marker PnP Fusion (primary) / Single-Marker fallback
---------------------------------------------------------------------
When multiple markers are visible the node collects ALL 4 corner pixel
coordinates from every accepted marker and feeds them into ONE combined
cv2.solvePnPRansac call.

  n visible markers → 4n image points  (2D, pixels)
                    → 4n object points (3D, map frame)
                    → cv2.solvePnPRansac
                    → single camera pose in map
                    → T_map_base = T_map_cam × T_cam_base

Why this is better than fusing separate poses in the EKF
---------------------------------------------------------
  • Pose ambiguity ("flip") is eliminated because the wider spread of
    corners from multiple markers constrains all 6 DOF simultaneously.
  • The EKF sees exactly ONE Gaussian measurement per cycle instead of
    N noisy, potentially contradicting ones.
  • RANSAC rejects any single corrupted corner set automatically.

Single-marker mode
------------------
  When only one marker is visible (or multi_marker_pnp: false) the node
  falls back to the same solvePnP call on just the 4 corners of that
  marker, which is still better than trusting aruco_ros's internal pose
  estimate directly, because we control the camera model and distortion.

Pipeline
--------
  /camera_00/rgb/image_raw   ──▶  aruco_ros  ──▶  /aruco/markers
  /camera_00/rgb/camera_info ──────────────────▶  [this node] K, D
                                                          │
                              landmarks.yaml ─────────────┤  world corners
                              tf2 static (cam→base) ──────┤
                                                          │
                                              /aruco/pose          → EKF pose0
                                              /aruco/detections    → GUI / log
                                              /aruco/status        → BT planner
                                              /aruco/reset_localization → srv

Math
----
  solvePnP:  [rvec, tvec] = f(obj_pts_map, img_pts_pixel, K, D)
             → T_cam_map  (OpenCV: p_cam = R @ p_map + t)
  T_map_cam  = inv(T_cam_map)
  T_map_base = T_map_cam @ T_cam_base   (T_cam_base from tf2 static)

Covariance model (distance-scaled, per-marker count boosted)
-----------------------------------------------------------
  mean_distance = mean of all accepted markers' centre distances
  sigma_xy  = (cov_scale_xy  * mean_distance) / sqrt(n_markers) + sqrt(cov_fixed_xy)
  sigma_yaw = (cov_scale_yaw * mean_distance) / sqrt(n_markers) + sqrt(cov_fixed_yaw)
  More markers → lower covariance → EKF weights correction more heavily.

Parameters (see aruco_localization.yaml)
"""

import math
import threading
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import yaml

import rclpy
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import ReentrantCallbackGroup, MutuallyExclusiveCallbackGroup
from rclpy.node import Node

from geometry_msgs.msg import (
    Pose,
    PoseWithCovarianceStamped,
    TransformStamped,
)
from sensor_msgs.msg import CameraInfo
from std_srvs.srv import Trigger

try:
    from aruco_msgs.msg import MarkerArray as ArucoMarkerArray
    _ARUCO_MSGS_AVAILABLE = True
except ImportError:
    _ARUCO_MSGS_AVAILABLE = False

import tf2_ros
import tf2_geometry_msgs  # noqa: F401

from rex_interfaces.msg import ArucoDetection, ArucoStatus


# ===========================================================================
# Constants: ArUco corner order (OpenCV convention, marker-local frame)
# Origin at marker centre, X right, Y up, Z out of board face.
# Corners returned by aruco_ros follow this order.
# ===========================================================================
#          Corner 0      Corner 1
#          top-left      top-right
#               ┌────────────┐
#               │            │
#               │   marker   │
#               │            │
#               └────────────┘
#          bottom-left   bottom-right
#          Corner 3      Corner 2
#
# Local 3D positions (z=0, marker lies in XY plane):

def _local_corners(half: float) -> np.ndarray:
    """Return (4,3) array of corner positions in the marker's local frame."""
    return np.array([
        [-half,  half, 0.0],   # 0: top-left
        [ half,  half, 0.0],   # 1: top-right
        [ half, -half, 0.0],   # 2: bottom-right
        [-half, -half, 0.0],   # 3: bottom-left
    ], dtype=np.float64)


# ===========================================================================
# Pure-math helpers (no ROS dependencies)
# ===========================================================================

def _euler_to_rotation_matrix(roll: float, pitch: float, yaw: float) -> np.ndarray:
    cr, sr = math.cos(roll),  math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw),   math.sin(yaw)
    return np.array([
        [cy*cp,  cy*sp*sr - sy*cr,  cy*sp*cr + sy*sr],
        [sy*cp,  sy*sp*sr + cy*cr,  sy*sp*cr - cy*sr],
        [-sp,    cp*sr,             cp*cr           ],
    ])


def _rotation_matrix_to_yaw(R: np.ndarray) -> float:
    return math.atan2(R[1, 0], R[0, 0])


def _se3_to_pose(T: np.ndarray) -> Pose:
    """4×4 SE3 → geometry_msgs/Pose (quaternion)."""
    R = T[:3, :3]
    trace = R[0, 0] + R[1, 1] + R[2, 2]
    if trace > 0:
        s = 0.5 / math.sqrt(trace + 1.0)
        w = 0.25 / s; x = (R[2,1]-R[1,2])*s; y = (R[0,2]-R[2,0])*s; z = (R[1,0]-R[0,1])*s
    elif R[0,0] > R[1,1] and R[0,0] > R[2,2]:
        s = 2.0 * math.sqrt(1.0 + R[0,0] - R[1,1] - R[2,2])
        w = (R[2,1]-R[1,2])/s; x = 0.25*s; y = (R[0,1]+R[1,0])/s; z = (R[0,2]+R[2,0])/s
    elif R[1,1] > R[2,2]:
        s = 2.0 * math.sqrt(1.0 + R[1,1] - R[0,0] - R[2,2])
        w = (R[0,2]-R[2,0])/s; x = (R[0,1]+R[1,0])/s; y = 0.25*s; z = (R[1,2]+R[2,1])/s
    else:
        s = 2.0 * math.sqrt(1.0 + R[2,2] - R[0,0] - R[1,1])
        w = (R[1,0]-R[0,1])/s; x = (R[0,2]+R[2,0])/s; y = (R[1,2]+R[2,1])/s; z = 0.25*s

    p = Pose()
    p.position.x    = float(T[0, 3]); p.position.y = float(T[1, 3]); p.position.z = float(T[2, 3])
    p.orientation.x = x; p.orientation.y = y; p.orientation.z = z; p.orientation.w = w
    return p


def _landmark_to_se3(entry: dict) -> np.ndarray:
    R = _euler_to_rotation_matrix(
        float(entry.get('roll',  0.0)),
        float(entry.get('pitch', 0.0)),
        float(entry.get('yaw',   0.0)),
    )
    T = np.eye(4)
    T[:3, :3] = R
    T[0, 3] = float(entry.get('x', 0.0))
    T[1, 3] = float(entry.get('y', 0.0))
    T[2, 3] = float(entry.get('z', 0.0))
    return T


def _tf_to_se3(tf_stamped: TransformStamped) -> np.ndarray:
    t = tf_stamped.transform.translation
    q = tf_stamped.transform.rotation
    x, y, z, w = q.x, q.y, q.z, q.w
    R = np.array([
        [1-2*(y*y+z*z),   2*(x*y-z*w),   2*(x*z+y*w)],
        [  2*(x*y+z*w), 1-2*(x*x+z*z),   2*(y*z-x*w)],
        [  2*(x*z-y*w),   2*(y*z+x*w), 1-2*(x*x+y*y)],
    ])
    T = np.eye(4)
    T[:3, :3] = R
    T[0, 3] = t.x; T[1, 3] = t.y; T[2, 3] = t.z
    return T


# ===========================================================================
# Node
# ===========================================================================

class ArucoLocalizationNode(Node):
    """
    Multi-marker PnP localization node.

    Collects pixel corners from all accepted ArUco markers visible in a frame,
    maps them to known 3D world positions via landmarks.yaml, then calls
    cv2.solvePnPRansac once to get the camera's exact pose in the map frame.
    """

    def __init__(self):
        super().__init__('aruco_localization_node')
        self._lock = threading.Lock()

        # ── Parameters ────────────────────────────────────────────────────
        self.declare_parameter('landmarks_file',             '')
        self.declare_parameter('camera_frame',               'camera_00_rgb_camera_optical_frame')
        self.declare_parameter('base_frame',                 'base_link')
        self.declare_parameter('map_frame',                  'map')
        self.declare_parameter('min_confidence',             0.65)
        self.declare_parameter('max_detection_distance_m',   10.0)
        self.declare_parameter('max_reprojection_error_px',  3.0)
        self.declare_parameter('max_pose_jump_m',            2.0)
        self.declare_parameter('max_pose_jump_yaw_rad',      0.52)
        self.declare_parameter('cov_scale_xy',               0.015)
        self.declare_parameter('cov_scale_yaw',              0.005)
        self.declare_parameter('cov_fixed_xy',               0.0001)
        self.declare_parameter('cov_fixed_yaw',              0.0001)
        self.declare_parameter('queue_size',                 5)
        self.declare_parameter('status_publish_rate_hz',     5.0)
        self.declare_parameter('publish_tf',                 False)
        # Multi-marker PnP parameters
        self.declare_parameter('use_multi_marker_pnp',       True)
        self.declare_parameter('use_ransac',                 True)
        self.declare_parameter('ransac_reprojection_threshold', 3.0)
        self.declare_parameter('ransac_min_inlier_ratio',    0.6)
        self.declare_parameter('pnp_flags',                  'SOLVEPNP_ITERATIVE')

        lm_file            = self.get_parameter('landmarks_file').value
        self._cam_fr       = self.get_parameter('camera_frame').value
        self._base_fr      = self.get_parameter('base_frame').value
        self._map_fr       = self.get_parameter('map_frame').value
        self._min_conf     = self.get_parameter('min_confidence').value
        self._max_dist     = self.get_parameter('max_detection_distance_m').value
        self._max_reproj   = self.get_parameter('max_reprojection_error_px').value
        self._max_jump_m   = self.get_parameter('max_pose_jump_m').value
        self._max_jump_yaw = self.get_parameter('max_pose_jump_yaw_rad').value
        self._cov_s_xy     = self.get_parameter('cov_scale_xy').value
        self._cov_s_yaw    = self.get_parameter('cov_scale_yaw').value
        self._cov_f_xy     = self.get_parameter('cov_fixed_xy').value
        self._cov_f_yaw    = self.get_parameter('cov_fixed_yaw').value
        self._q_sz         = self.get_parameter('queue_size').value
        self._status_rate  = self.get_parameter('status_publish_rate_hz').value
        self._pub_tf       = self.get_parameter('publish_tf').value
        self._use_mm_pnp   = self.get_parameter('use_multi_marker_pnp').value
        self._use_ransac   = self.get_parameter('use_ransac').value
        self._ransac_thr   = self.get_parameter('ransac_reprojection_threshold').value
        self._ransac_inlier= self.get_parameter('ransac_min_inlier_ratio').value
        pnp_flag_str       = self.get_parameter('pnp_flags').value

        _pnp_map = {
            'SOLVEPNP_ITERATIVE': cv2.SOLVEPNP_ITERATIVE,
            'SOLVEPNP_SQPNP':    cv2.SOLVEPNP_SQPNP,
            'SOLVEPNP_EPNP':     cv2.SOLVEPNP_EPNP,
            'SOLVEPNP_AP3P':     cv2.SOLVEPNP_AP3P,
        }
        self._pnp_flags = _pnp_map.get(pnp_flag_str, cv2.SOLVEPNP_ITERATIVE)

        # ── Landmark database ─────────────────────────────────────────────
        # _landmarks[id]         : 4×4 SE3  (T_map_marker)
        # _world_corners[id]     : (4,3) np.ndarray — corners in map frame
        self._landmarks:     Dict[int, np.ndarray] = {}
        self._world_corners: Dict[int, np.ndarray] = {}
        self._marker_size = 0.150       # overwritten by landmarks.yaml
        self._load_landmarks(lm_file)

        # ── Camera intrinsics ─────────────────────────────────────────────
        self._K: Optional[np.ndarray] = None   # (3,3) camera matrix
        self._D: Optional[np.ndarray] = None   # distortion coefficients
        self._cam_info_ok = False

        # ── TF2 ───────────────────────────────────────────────────────────
        self._tf_buffer   = tf2_ros.Buffer()
        self._tf_listener = tf2_ros.TransformListener(self._tf_buffer, self)
        if self._pub_tf:
            self._tf_broadcaster = tf2_ros.TransformBroadcaster(self)

        # ── State ─────────────────────────────────────────────────────────
        self._last_pose: Optional[Tuple[float, float, float]] = None
        self._last_correction_time = rclpy.time.Time()
        self._localization_available = False
        self._last_visible_ids: List[int] = []
        self._last_best_id   = -1
        self._last_best_dist = 0.0
        self._last_best_conf = 0.0

        # ── Callback groups ───────────────────────────────────────────────
        self._cb_detect = ReentrantCallbackGroup()
        self._cb_info   = MutuallyExclusiveCallbackGroup()
        self._cb_timer  = MutuallyExclusiveCallbackGroup()
        self._cb_srv    = MutuallyExclusiveCallbackGroup()

        # ── Publishers ────────────────────────────────────────────────────
        self._pub_pose  = self.create_publisher(PoseWithCovarianceStamped, 'aruco/pose',       self._q_sz)
        self._pub_det   = self.create_publisher(ArucoDetection,            'aruco/detections', self._q_sz)
        self._pub_stat  = self.create_publisher(ArucoStatus,               'aruco/status',     self._q_sz)

        # ── Subscribers ───────────────────────────────────────────────────
        if _ARUCO_MSGS_AVAILABLE:
            self._sub_markers = self.create_subscription(
                ArucoMarkerArray, 'aruco/markers',
                self._markers_callback, self._q_sz,
                callback_group=self._cb_detect,
            )
        else:
            self.get_logger().error(
                '[aruco_localization] aruco_msgs not found! '
                'Install ros-jazzy-aruco-ros and rebuild.'
            )

        self._sub_info = self.create_subscription(
            CameraInfo,
            f'/{self._cam_fr.split("_")[0]}_00/rgb/camera_info',
            self._camera_info_callback, 1,
            callback_group=self._cb_info,
        )

        # ── Timers / Services ─────────────────────────────────────────────
        self.create_timer(
            1.0 / self._status_rate, self._publish_status,
            callback_group=self._cb_timer,
        )
        self.create_service(
            Trigger, 'aruco/reset_localization',
            self._reset_callback,
            callback_group=self._cb_srv,
        )

        mode = 'multi-marker PnP' if self._use_mm_pnp else 'single-marker PnP'
        self.get_logger().info(
            f'[aruco_localization] ready | mode: {mode} | '
            f'RANSAC: {self._use_ransac} | landmarks: {len(self._landmarks)}'
        )

    # ── Landmark loading ──────────────────────────────────────────────────

    def _load_landmarks(self, path: str) -> None:
        if not path:
            self.get_logger().warn('[aruco_localization] landmarks_file not set.')
            return
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f)
        except Exception as exc:
            self.get_logger().error(f'[aruco_localization] cannot load landmarks: {exc}')
            return

        self._marker_size = float(data.get('marker_size_m', 0.150))
        half = self._marker_size / 2.0
        local_c = _local_corners(half)

        for mid_raw, entry in data.get('landmarks', {}).items():
            mid = int(mid_raw)
            T   = _landmark_to_se3(entry)
            self._landmarks[mid]     = T
            # Pre-compute 3D world corner positions (used in PnP)
            # Each row: (T @ [local_corner, 1])[:3]
            world_c = (T[:3, :3] @ local_c.T).T + T[:3, 3]
            self._world_corners[mid] = world_c  # shape (4,3)

        self.get_logger().info(
            f'[aruco_localization] {len(self._landmarks)} landmarks loaded '
            f'(marker_size={self._marker_size}m) from {path}'
        )

    # ── Camera info ───────────────────────────────────────────────────────

    def _camera_info_callback(self, msg: CameraInfo) -> None:
        if self._cam_info_ok:
            return  # only need once
        self._K = np.array(msg.k, dtype=np.float64).reshape(3, 3)
        self._D = np.array(msg.d, dtype=np.float64)
        self._cam_info_ok = True
        self.get_logger().info(
            f'[aruco_localization] camera intrinsics received | '
            f'fx={self._K[0,0]:.1f} fy={self._K[1,1]:.1f} '
            f'cx={self._K[0,2]:.1f} cy={self._K[1,2]:.1f}'
        )

    # ── Main detection callback ───────────────────────────────────────────

    def _markers_callback(self, msg: 'ArucoMarkerArray') -> None:
        if not self._cam_info_ok:
            self.get_logger().warn(
                '[aruco_localization] waiting for camera_info …', throttle_duration_sec=5.0
            )
            with self._lock:
                self._localization_available = False
            return

        if not msg.markers:
            with self._lock:
                self._localization_available = False
                self._last_visible_ids = []
            return

        # ── Per-marker quality filter & detection publishing ──────────────
        accepted: List[dict] = []    # markers that pass all quality gates

        for marker in msg.markers:
            mid = int(marker.id)

            # Centre distance from aruco_ros pose (camera frame)
            p   = marker.pose.pose.position
            dist = math.sqrt(p.x**2 + p.y**2 + p.z**2)
            angle_deg = math.degrees(math.atan2(p.x, p.z))

            # Distance-based confidence (simple model — PnP reprojection
            # error is recomputed after solve for accepted groups)
            half_range = self._max_dist * 0.5
            conf = 1.0
            if dist > half_range:
                conf = max(0.0, 1.0 - (dist - half_range) / half_range)

            if dist <= self._max_dist and conf >= self._min_conf:
                quality = 'good'
            elif dist > self._max_dist:
                quality = 'rejected'
            else:
                quality = 'marginal'

            # Publish per-marker detection regardless of gate
            det = ArucoDetection()
            det.header              = msg.header
            det.marker_id           = mid
            det.distance_m          = dist
            det.angle_deg           = angle_deg
            det.pose_camera_frame   = marker.pose.pose
            det.reprojection_error_px = 0.0   # filled after PnP solve
            det.confidence          = conf
            det.quality             = quality
            self._pub_det.publish(det)

            if quality != 'good' or mid not in self._world_corners:
                if quality == 'good' and mid not in self._world_corners:
                    self.get_logger().warn(
                        f'[aruco_localization] marker {mid} detected '
                        f'but not in landmarks.yaml', throttle_duration_sec=10.0
                    )
                continue

            # Extract corner pixel coordinates from aruco_ros
            # aruco_msgs/Marker.corners: list of geometry_msgs/Point (z=0, pixel x/y)
            if not hasattr(marker, 'corners') or len(marker.corners) != 4:
                # Fallback: skip — aruco_ros should always provide 4 corners
                self.get_logger().warn(
                    f'[aruco_localization] marker {mid} has no corner data',
                    throttle_duration_sec=5.0
                )
                continue

            img_corners = np.array(
                [[c.x, c.y] for c in marker.corners], dtype=np.float64
            )   # shape (4, 2)

            accepted.append({
                'id':          mid,
                'distance':    dist,
                'confidence':  conf,
                'img_corners': img_corners,           # (4,2) pixels
                'world_corners': self._world_corners[mid],  # (4,3) map frame
            })

        with self._lock:
            self._last_visible_ids = [m['id'] for m in accepted]

        if not accepted:
            with self._lock:
                self._localization_available = False
            return

        # ── PnP solve ─────────────────────────────────────────────────────
        if self._use_mm_pnp and len(accepted) > 1:
            pose_msg, reproj_err, n_inliers = self._solve_multi_marker_pnp(
                accepted, msg.header.stamp
            )
            mode_str = f'multi-PnP ({len(accepted)} markers, {n_inliers} inliers)'
        else:
            # Single marker: pick highest confidence
            best = max(accepted, key=lambda m: m['confidence'])
            pose_msg, reproj_err, n_inliers = self._solve_single_marker_pnp(
                best, msg.header.stamp
            )
            mode_str = f'single-PnP (marker {best["id"]})'

        if pose_msg is None:
            return

        # ── Outlier rejection (pose-jump gate) ────────────────────────────
        T_est = self._pose_to_se3_from_msg(pose_msg.pose.pose)
        x   = pose_msg.pose.pose.position.x
        y   = pose_msg.pose.pose.position.y
        yaw = _rotation_matrix_to_yaw(T_est[:3, :3])

        with self._lock:
            last = self._last_pose

        if last is not None:
            dx   = abs(x - last[0])
            dy   = abs(y - last[1])
            dyaw = abs(yaw - last[2])
            if dx > self._max_jump_m or dy > self._max_jump_m or dyaw > self._max_jump_yaw:
                self.get_logger().warn(
                    f'[aruco_localization] jump rejected: '
                    f'Δ=({dx:.2f}m, {dy:.2f}m, {math.degrees(dyaw):.1f}°) | '
                    f'Use /aruco/reset_localization to clear gate.'
                )
                return

        # ── Accept & publish ──────────────────────────────────────────────
        best_marker = max(accepted, key=lambda m: m['confidence'])
        with self._lock:
            self._last_pose              = (x, y, yaw)
            self._last_correction_time   = self.get_clock().now()
            self._localization_available = True
            self._last_best_id           = best_marker['id']
            self._last_best_dist         = best_marker['distance']
            self._last_best_conf         = best_marker['confidence']

        self._pub_pose.publish(pose_msg)

        if self._pub_tf:
            self._broadcast_tf(pose_msg)

        self.get_logger().debug(
            f'[aruco_localization] {mode_str} | '
            f'reproj={reproj_err:.2f}px | '
            f'pose=({x:.2f}, {y:.2f}, {math.degrees(yaw):.1f}°)'
        )

    # ── Multi-marker PnP ─────────────────────────────────────────────────

    def _solve_multi_marker_pnp(
        self,
        markers: List[dict],
        stamp,
    ) -> Tuple[Optional[PoseWithCovarianceStamped], float, int]:
        """
        Combine corners from all accepted markers into one solvePnP call.

        Returns (PoseWithCovarianceStamped | None, mean_reproj_error, n_inliers)
        """
        # Stack all corners
        obj_pts = np.vstack([m['world_corners'] for m in markers])   # (4n, 3)
        img_pts = np.vstack([m['img_corners']   for m in markers])   # (4n, 2)

        obj_pts = obj_pts.reshape(-1, 1, 3).astype(np.float64)
        img_pts = img_pts.reshape(-1, 1, 2).astype(np.float64)

        rvec, tvec, inliers, reproj_err = self._run_pnp(obj_pts, img_pts)
        if rvec is None:
            return None, 0.0, 0

        n_total  = len(obj_pts)
        n_inlier = len(inliers) if inliers is not None else n_total

        # RANSAC inlier ratio check
        if inliers is not None and (n_inlier / n_total) < self._ransac_inlier:
            self.get_logger().warn(
                f'[aruco_localization] multi-PnP inlier ratio too low: '
                f'{n_inlier}/{n_total} < {self._ransac_inlier:.0%}'
            )
            return None, reproj_err, n_inlier

        pose_msg = self._build_pose_msg(rvec, tvec, markers, stamp)
        return pose_msg, reproj_err, n_inlier

    # ── Single-marker PnP ────────────────────────────────────────────────

    def _solve_single_marker_pnp(
        self,
        marker: dict,
        stamp,
    ) -> Tuple[Optional[PoseWithCovarianceStamped], float, int]:
        obj_pts = marker['world_corners'].reshape(-1, 1, 3).astype(np.float64)
        img_pts = marker['img_corners'].reshape(-1, 1, 2).astype(np.float64)

        rvec, tvec, inliers, reproj_err = self._run_pnp(obj_pts, img_pts)
        if rvec is None:
            return None, 0.0, 0

        pose_msg = self._build_pose_msg(rvec, tvec, [marker], stamp)
        return pose_msg, reproj_err, 4

    # ── OpenCV PnP wrapper ────────────────────────────────────────────────

    def _run_pnp(
        self,
        obj_pts: np.ndarray,
        img_pts: np.ndarray,
    ) -> Tuple[Optional[np.ndarray], Optional[np.ndarray], Optional[np.ndarray], float]:
        """
        Run solvePnP(Ransac).
        Returns (rvec, tvec, inliers | None, mean_reprojection_error).
        All return values None on failure.
        """
        try:
            if self._use_ransac:
                ok, rvec, tvec, inliers = cv2.solvePnPRansac(
                    obj_pts, img_pts, self._K, self._D,
                    reprojectionError=self._ransac_thr,
                    confidence=0.99,
                    iterationsCount=300,
                    flags=self._pnp_flags,
                )
            else:
                ok, rvec, tvec = cv2.solvePnP(
                    obj_pts, img_pts, self._K, self._D,
                    flags=self._pnp_flags,
                )
                inliers = None

            if not ok:
                return None, None, None, 0.0

            # Compute mean reprojection error with final pose
            proj, _ = cv2.projectPoints(obj_pts, rvec, tvec, self._K, self._D)
            reproj_err = float(np.mean(np.linalg.norm(
                img_pts.reshape(-1, 2) - proj.reshape(-1, 2), axis=1
            )))

            if reproj_err > self._max_reproj:
                self.get_logger().warn(
                    f'[aruco_localization] PnP reproj error {reproj_err:.2f}px '
                    f'> threshold {self._max_reproj:.2f}px — rejected'
                )
                return None, None, None, reproj_err

            return rvec, tvec, inliers, reproj_err

        except cv2.error as exc:
            self.get_logger().warn(f'[aruco_localization] cv2 PnP failed: {exc}')
            return None, None, None, 0.0

    # ── Build PoseWithCovarianceStamped from PnP result ───────────────────

    def _build_pose_msg(
        self,
        rvec: np.ndarray,
        tvec: np.ndarray,
        markers: List[dict],
        stamp,
    ) -> Optional[PoseWithCovarianceStamped]:
        """
        Convert solvePnP output → map-frame PoseWithCovarianceStamped.

        solvePnP returns T_cam_map  (p_cam = R @ p_map + t)
        We need:       T_map_base = T_map_cam × T_cam_base
        """
        # T_cam_map from Rodrigues
        R_cm, _ = cv2.Rodrigues(rvec)
        T_cam_map = np.eye(4)
        T_cam_map[:3, :3] = R_cm
        T_cam_map[:3,  3] = tvec.flatten()

        T_map_cam = np.linalg.inv(T_cam_map)

        # T_cam_base from TF tree
        try:
            tf_s = self._tf_buffer.lookup_transform(
                self._cam_fr, self._base_fr,
                rclpy.time.Time(),
                timeout=rclpy.duration.Duration(seconds=0.2),
            )
        except (tf2_ros.LookupException,
                tf2_ros.ConnectivityException,
                tf2_ros.ExtrapolationException) as exc:
            self.get_logger().warn(
                f'[aruco_localization] TF {self._cam_fr}→{self._base_fr}: {exc}'
            )
            return None

        T_cam_base = _tf_to_se3(tf_s)
        T_map_base = T_map_cam @ T_cam_base

        # ── Distance-scaled covariance (boosted by marker count) ──────────
        mean_dist = float(np.mean([m['distance'] for m in markers]))
        n_m       = len(markers)
        inv_sqrt_n = 1.0 / math.sqrt(n_m)

        var_xy  = (self._cov_s_xy  * mean_dist * inv_sqrt_n) ** 2 + self._cov_f_xy
        var_yaw = (self._cov_s_yaw * mean_dist * inv_sqrt_n) ** 2 + self._cov_f_yaw

        cov = [0.0] * 36
        cov[0]  = var_xy
        cov[7]  = var_xy
        cov[14] = 1e6      # z  — ignored by EKF (2D mode)
        cov[21] = 1e6      # roll
        cov[28] = 1e6      # pitch
        cov[35] = var_yaw

        msg = PoseWithCovarianceStamped()
        msg.header.stamp    = stamp
        msg.header.frame_id = self._map_fr
        msg.pose.pose       = _se3_to_pose(T_map_base)
        msg.pose.covariance = cov
        return msg

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _pose_to_se3_from_msg(pose: Pose) -> np.ndarray:
        q = pose.orientation
        x, y, z, w = q.x, q.y, q.z, q.w
        R = np.array([
            [1-2*(y*y+z*z),   2*(x*y-z*w),   2*(x*z+y*w)],
            [  2*(x*y+z*w), 1-2*(x*x+z*z),   2*(y*z-x*w)],
            [  2*(x*z-y*w),   2*(y*z+x*w), 1-2*(x*x+y*y)],
        ])
        T = np.eye(4)
        T[:3, :3] = R
        T[0, 3] = pose.position.x
        T[1, 3] = pose.position.y
        T[2, 3] = pose.position.z
        return T

    def _broadcast_tf(self, pose_msg: PoseWithCovarianceStamped) -> None:
        ts = TransformStamped()
        ts.header         = pose_msg.header
        ts.child_frame_id = self._base_fr
        p = pose_msg.pose.pose.position
        q = pose_msg.pose.pose.orientation
        ts.transform.translation.x = p.x
        ts.transform.translation.y = p.y
        ts.transform.translation.z = p.z
        ts.transform.rotation      = q
        self._tf_broadcaster.sendTransform(ts)

    # ── Status publisher ──────────────────────────────────────────────────

    def _publish_status(self) -> None:
        with self._lock:
            available  = self._localization_available
            last_time  = self._last_correction_time
            last_pose  = self._last_pose
            visible    = list(self._last_visible_ids)
            best_id    = self._last_best_id
            best_dist  = self._last_best_dist
            best_conf  = self._last_best_conf

        msg = ArucoStatus()
        msg.header.stamp           = self.get_clock().now().to_msg()
        msg.header.frame_id        = self._map_fr
        msg.visible_marker_ids     = visible
        msg.best_marker_id         = best_id
        msg.best_marker_distance_m = best_dist
        msg.best_marker_confidence = best_conf
        msg.localization_available = available
        msg.last_correction_time   = last_time.to_msg()

        if available and last_pose:
            msg.status_message = (
                f'OK [{len(visible)} marker(s)] | '
                f'pos=({last_pose[0]:.2f},{last_pose[1]:.2f},'
                f'{math.degrees(last_pose[2]):.1f}°)'
            )
        elif not self._cam_info_ok:
            msg.status_message = 'Waiting for camera_info'
        else:
            msg.status_message = 'No valid marker visible'

        self._pub_stat.publish(msg)

    # ── Reset service ─────────────────────────────────────────────────────

    def _reset_callback(
        self,
        request: Trigger.Request,
        response: Trigger.Response,
    ) -> Trigger.Response:
        with self._lock:
            self._last_pose              = None
            self._last_correction_time   = rclpy.time.Time()
            self._localization_available = False
        self.get_logger().info('[aruco_localization] state reset via service')
        response.success = True
        response.message = (
            'Jump gate cleared. Next valid PnP solve accepted unconditionally.'
        )
        return response


# ===========================================================================
# Entry point
# ===========================================================================

def main(args=None):
    rclpy.init(args=args)
    node = ArucoLocalizationNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
