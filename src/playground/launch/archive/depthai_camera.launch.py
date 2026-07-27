import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    OpaqueFunction,
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import ComposableNodeContainer, LoadComposableNodes, Node
from launch_ros.descriptions import ComposableNode, ParameterFile
from launch_ros.substitutions import FindPackageShare


def is_launch_config_true(context, name):
    return LaunchConfiguration(name).perform(context) == "true"


def setup_launch_prefix(context, *args, **kwargs):
    use_gdb = LaunchConfiguration("use_gdb", default="false")
    use_valgrind = LaunchConfiguration("use_valgrind", default="false")
    use_perf = LaunchConfiguration("use_perf", default="false")

    launch_prefix = ""

    if use_gdb.perform(context) == "true":
        launch_prefix += "xterm -e gdb -ex run --args"
    if use_valgrind.perform(context) == "true":
        launch_prefix += "valgrind --tool=callgrind"
    if use_perf.perform(context) == "true":
        launch_prefix += (
            "perf record -g --call-graph dwarf --output=perf.out.node_name.data --"
        )

    return launch_prefix


def launch_setup(context, *args, **kwargs):
    valid_log_levels = ["debug", "info", "warn", "error", "fatal"]

    log_level = LaunchConfiguration(
        "log_level", default="info"
    ).perform(context)

    if log_level not in valid_log_levels:
        log_level = "info"

    #--

    params_file = ParameterFile(LaunchConfiguration("params_file"), allow_substs=True)
    
    #--

    publish_tf_from_calibration = LaunchConfiguration("publish_tf_from_calibration", default="false")

    namespace    = LaunchConfiguration("namespace",    default="").perform(context)
    name         = LaunchConfiguration("name",         default="oak").perform(context)
    camera_model = LaunchConfiguration("camera_model", default="OAK-D-PRO").perform(context)
    parent_frame = LaunchConfiguration("parent_frame", default="oak-d-base-frame").perform(context)
    base_frame   = LaunchConfiguration("base_frame",   default="oak").perform(context)
    cam_pos_x = LaunchConfiguration("cam_pos_x", default="0.0").perform(context)
    cam_pos_y = LaunchConfiguration("cam_pos_y", default="0.0").perform(context)
    cam_pos_z = LaunchConfiguration("cam_pos_z", default="0.0").perform(context)
    cam_roll  = LaunchConfiguration("cam_roll",  default="0.0").perform(context)
    cam_pitch = LaunchConfiguration("cam_pitch", default="0.0").perform(context)
    cam_yaw   = LaunchConfiguration("cam_yaw",   default="0.0").perform(context)

    #--

    use_composition = LaunchConfiguration("use_composition", default="true").perform(context)

    #--

    use_node_composition = LaunchConfiguration("use_node_composition", default="false")

    #--

    launch_prefix = setup_launch_prefix(context)

    return [
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([
                    FindPackageShare("playground"),
                    "launch",
                    "depthai_camera_description.launch.py"
                ])
            ),
            launch_arguments={
                "namespace":    namespace,
                "name":         name,
                "camera_model": camera_model,
                "base_frame":   base_frame,
                "parent_frame": parent_frame,
                "cam_pos_x": cam_pos_x,
                "cam_pos_y": cam_pos_y,
                "cam_pos_z": cam_pos_z,
                "cam_roll":  cam_roll,
                "cam_pitch": cam_pitch,
                "cam_yaw":   cam_yaw,
                "use_node_composition": use_node_composition,
            }.items(),
        ),

        ComposableNodeContainer(
            name=f"{name}_container",
            namespace=namespace,
            package="rclcpp_components",
            executable="component_container",
            composable_node_descriptions=[
                ComposableNode(
                    package="depthai_ros_driver",
                    plugin="depthai_ros_driver::Camera",
                    name=name,
                    namespace=namespace,
                    parameters=[
                        params_file,
                    ],
                )
            ],
            arguments=["--ros-args", "--log-level", log_level],
            prefix=[launch_prefix],
            output="both",
        ),
    ]


def generate_launch_description():
    depthai_prefix = get_package_share_directory("depthai_ros_driver")

    declared_arguments = [

        DeclareLaunchArgument("log_level", default_value="info"),

        DeclareLaunchArgument(
            "params_file",
            default_value=os.path.join(depthai_prefix, "config", "camera.yaml"),
        ),

        DeclareLaunchArgument("publish_tf_from_calibration", default_value="false",),

        DeclareLaunchArgument("namespace",    default_value=""),
        DeclareLaunchArgument("name",         default_value="oak"),
        DeclareLaunchArgument("camera_model", default_value="OAK-D-PRO"),
        DeclareLaunchArgument("parent_frame", default_value="oak-d-base-frame"),
        DeclareLaunchArgument("base_frame",   default_value="oak"),
        DeclareLaunchArgument("cam_pos_x", default_value="0.0"),
        DeclareLaunchArgument("cam_pos_y", default_value="0.0"),
        DeclareLaunchArgument("cam_pos_z", default_value="0.0"),
        DeclareLaunchArgument("cam_roll",  default_value="0.0"),
        DeclareLaunchArgument("cam_pitch", default_value="0.0"),
        DeclareLaunchArgument("cam_yaw",   default_value="0.0"),

        DeclareLaunchArgument("use_gdb", default_value="false"),
        DeclareLaunchArgument("use_valgrind", default_value="false"),
        DeclareLaunchArgument("use_perf", default_value="false"),

        DeclareLaunchArgument(
            "use_node_composition",
            default_value="false",
            description="",
        ),
    ]

    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )
