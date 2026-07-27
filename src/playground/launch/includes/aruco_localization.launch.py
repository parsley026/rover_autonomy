"""
aruco_localization.launch.py
============================
Launches the ArUco marker detection and pose localization pipeline:

  1. aruco_ros / aruco_opencv  (marker detection, DICT_5X5_100)
     subscribes:  /<camera_ns>/rgb/image_raw
                  /<camera_ns>/rgb/camera_info
     publishes:   /aruco/markers  (aruco_msgs/ArucoMarkerArray)

  2. aruco_localization_node  (custom pose computation node)
     subscribes:  /aruco/markers
     publishes:   /aruco/pose          → robot_localization EKF pose0
                  /aruco/detections    → operator GUI / logger
                  /aruco/status        → behaviour tree / planner
     service:     /aruco/reset_localization

Arguments
---------
  camera_ns       : camera namespace (default: camera_00)
  params_file     : path to aruco_localization.yaml
  landmarks_file  : path to landmarks.yaml
  use_sim_time    : bool (default: false)

Config flow
-----------
  bringup_profile.yaml
      aruco_config    → params_file
      aruco_landmarks → landmarks_file
          ↓
  bringup.launch.py (reads + forwards)
          ↓
  aruco_localization.launch.py (this file)
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def launch_setup(context, *args, **kwargs):
    camera_ns      = LaunchConfiguration('camera_ns').perform(context)
    params_file    = LaunchConfiguration('params_file').perform(context)
    landmarks_file = LaunchConfiguration('landmarks_file').perform(context)
    use_sim_time   = LaunchConfiguration('use_sim_time').perform(context).lower() == 'true'

    pkg_share = get_package_share_directory('playground')

    # Resolve params_file relative to package share if not absolute
    if not os.path.isabs(params_file):
        params_file = os.path.join(pkg_share, params_file)

    # Resolve landmarks_file relative to package share if not absolute
    if not os.path.isabs(landmarks_file):
        landmarks_file = os.path.join(pkg_share, landmarks_file)

    # -----------------------------------------------------------------------
    # Node 1: aruco_ros detector
    # -----------------------------------------------------------------------
    # aruco_ros single node: consumes camera image + info,
    # publishes /aruco/markers (ArucoMarkerArray).
    #
    # Parameters:
    #   image_is_rectified : true  — assumes camera_00 publishes rectified images
    #   marker_size        : 0.150 — 150 mm markers
    #   : DICT_5X5_100 (competition spec)
    #   camera_frame       : camera_00_rgb_camera_optical_frame (depthai default)
    #
    # Remappings bridge from the camera driver's topic names to the
    # aruco_ros expected topic names.
    # -----------------------------------------------------------------------
    aruco_detector_node = Node(
        package='aruco_ros',
        executable='marker_publisher',
        name='aruco_detector',
        namespace='aruco',
        parameters=[{
            'image_is_rectified': True,
            'marker_size':        0.150,
            'aruco_dictionary_id': 'DICT_5X5_1000',
            'camera_frame':       f'{camera_ns}_rgb_camera_optical_frame',
            'use_sim_time':       use_sim_time,
        }],
        remappings=[
            ('/image',       f'/{camera_ns}/rgb/image_raw'),
            ('/camera_info', f'/{camera_ns}/rgb/camera_info'),
        ],
        output='screen',
    )

    # -----------------------------------------------------------------------
    # Node 2: ArUco localization (custom pose computation node)
    # -----------------------------------------------------------------------
    aruco_localization_node = Node(
        package='playground',
        executable='aruco_localization_node',
        name='aruco_localization_node',
        namespace='',              # global namespace — publishes to /aruco/pose etc.
        parameters=[
            params_file,
            {
                'landmarks_file': landmarks_file,
                'camera_frame':   f'{camera_ns}_rgb_camera_optical_frame',
                'use_sim_time':   use_sim_time,
            },
        ],
        remappings=[
            ('aruco/markers', '/aruco/markers'),
        ],
        output='screen',
    )

    return [aruco_detector_node, aruco_localization_node]


def generate_launch_description():
    pkg_share = get_package_share_directory('playground')

    default_params    = os.path.join(
        pkg_share, 'config', 'localization', 'aruco_localization.yaml'
    )
    default_landmarks = os.path.join(
        pkg_share, 'config', 'localization', 'landmarks.yaml'
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'camera_ns',
            default_value='camera_00',
            description='Camera namespace (must match depthai driver namespace)',
        ),
        DeclareLaunchArgument(
            'params_file',
            default_value=default_params,
            description='Path to aruco_localization.yaml',
        ),
        DeclareLaunchArgument(
            'landmarks_file',
            default_value=default_landmarks,
            description='Path to landmarks.yaml marker database',
        ),
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation clock',
        ),
        OpaqueFunction(function=launch_setup),
    ])
