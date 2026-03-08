from launch.actions import TimerAction
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, IncludeLaunchDescription
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, Command, FindExecutable, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import LoadComposableNodes, Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.descriptions import ComposableNode
from launch_ros.parameter_descriptions import ParameterValue

def launch_setup(context, *args, **kwargs):

    return [
        TimerAction(
            period=0.0,
            actions=[
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([
                            FindPackageShare("playground"),
                            "launch",
                            "sensors_mounts_description.launch.py"
                        ])
                    ),
                    launch_arguments={
                        "namespace":            "mounts",
                        "name":                 "mounts",
                        "use_node_composition": "false",
                    }.items(),
                ),
            ]
        ),
        TimerAction(
            period=5.0,
            actions=[
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([
                            FindPackageShare("playground"),
                            "launch",
                            "depthai_camera.launch.py"
                        ])
                    ),
                    launch_arguments={
                        "params_file":  "/home/rex/raptor_ws/src/playground/config/oak_d.yaml",
                        "namespace":    "oak_d",
                        "name":         "oak_d",
                        "camera_model": "OAK-D",
                        "base_frame":   "oak-d-link",
                        "parent_frame": "sensor-mount-00-link",
                        "cam_pos_x": "0.0",
                        "cam_pos_y": "0.0",
                        "cam_pos_z": "0.0",
                        "cam_roll":  "0.0",
                        "cam_pitch": "0.0",
                        "cam_yaw":   "0.0",
                        "use_node_composition": "false",
                    }.items(),
                ),
            ]
        ),
        TimerAction(
            period=10.0,
            actions=[
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([
                            FindPackageShare("playground"),
                            "launch",
                            "depthai_camera.launch.py"
                        ])
                    ),
                    launch_arguments={
                        "params_file":  "/home/rex/raptor_ws/src/playground/config/oak_d_pro.yaml",
                        "namespace":    "oak_d_pro",
                        "name":         "oak_d_pro",
                        "camera_model": "OAK-D-PRO",
                        "base_frame":   "oak-d-pro-link",
                        "parent_frame": "sensor-mount-01-link",
                        "cam_pos_x": "0.0",
                        "cam_pos_y": "0.0",
                        "cam_pos_z": "0.0",
                        "cam_roll":  "0.0",
                        "cam_pitch": "0.0",
                        "cam_yaw":   "0.0",
                        "use_node_composition": "false",
                    }.items(),
                )
            ]
        ),
        TimerAction(
            period=15.0,
            actions=[
                IncludeLaunchDescription(
                    PythonLaunchDescriptionSource(
                        PathJoinSubstitution([
                            FindPackageShare("playground"),
                            "launch",
                            "ouster_lidar.launch.py"
                        ])
                    ),
                    launch_arguments={
                        "params_file":  "/home/rex/raptor_ws/src/playground/config/ouster_os.yaml",
                        "ouster_ns": "ouster_os",
                    }.items(),
                )
            ]
        )
    ]


def generate_launch_description():
    declared_arguments = [

    ]

    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )
    