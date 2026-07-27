import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, Command, FindExecutable, PathJoinSubstitution
from launch_ros.actions import LoadComposableNodes, Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.descriptions import ComposableNode
from launch_ros.parameter_descriptions import ParameterValue


def launch_setup(context, *args, **kwargs):
    xacro_file = LaunchConfiguration("xacro_file", default=PathJoinSubstitution(
                [FindPackageShare('playground'),
                "urdf",
                "depthai_camera_description.urdf.xacro"
                ]
            ),)

    namespace    = LaunchConfiguration("namespace",    default="")
    name         = LaunchConfiguration("name",         default="oak").perform(context)
    camera_model = LaunchConfiguration("camera_model", default="OAK-D").perform(context)
    parent_frame = LaunchConfiguration("parent_frame", default="oak-d-base-frame").perform(context)
    base_frame   = LaunchConfiguration("base_frame",   default="oak").perform(context)
    cam_pos_x = LaunchConfiguration("cam_pos_x", default="0.0").perform(context)
    cam_pos_y = LaunchConfiguration("cam_pos_y", default="0.0").perform(context)
    cam_pos_z = LaunchConfiguration("cam_pos_z", default="0.0").perform(context)
    cam_roll  = LaunchConfiguration("cam_roll",  default="1.5708").perform(context)
    cam_pitch = LaunchConfiguration("cam_pitch", default="0.0").perform(context)
    cam_yaw   = LaunchConfiguration("cam_yaw",   default="1.5708").perform(context)

    use_node_composition = LaunchConfiguration("use_node_composition", default="false").perform(context)

    robot_description = {
        'robot_description': ParameterValue(
            Command([
                FindExecutable(name='xacro'),
                ' ',
                xacro_file,
                f" camera_name:={name}",
                f" camera_model:={camera_model}",
                f" base_frame:={base_frame}",
                f" parent_frame:={parent_frame}",
                f" cam_pos_x:={cam_pos_x}",
                f" cam_pos_y:={cam_pos_y}",
                f" cam_pos_z:={cam_pos_z}",
                f" cam_roll:={cam_roll}",
                f" cam_pitch:={cam_pitch}",
                f" cam_yaw:={cam_yaw}",
            ]),
            value_type=str,
        )
    }

    return [
        Node(
            package="robot_state_publisher",
            condition=UnlessCondition(use_node_composition),
            executable="robot_state_publisher",
            name=name + "_state_publisher",
            namespace=namespace,
            parameters=[robot_description],
        ),
        LoadComposableNodes(
            target_container=f"{namespace.perform(context)}/{name}_container",
            condition=IfCondition(use_node_composition),
            composable_node_descriptions=[
                ComposableNode(
                    package="robot_state_publisher",
                    plugin="robot_state_publisher::RobotStatePublisher",
                    name=name + "_state_publisher",
                    namespace=namespace,
                    parameters=[robot_description],
                )
            ],
        ),
    ]


def generate_launch_description():
    declared_arguments = [
        DeclareLaunchArgument(
            "xacro_file",
            default_value=PathJoinSubstitution(
                [FindPackageShare('playground'),
                "urdf",
                "depthai_camera_description.urdf.xacro"
                ]
            ),
            description=""
        ),
        DeclareLaunchArgument(
            "namespace",
            default_value="",
            description="",
        ),
        DeclareLaunchArgument(
            "name",
            default_value="oak",
            description="",
        ),
        DeclareLaunchArgument(
            "camera_model",
            default_value="OAK-D",
            description="",
        ),
        DeclareLaunchArgument(
            "base_frame",
            default_value="oak",
            description="",
        ),
        DeclareLaunchArgument(
            "parent_frame",
            default_value="oak-d-base-frame",
            description="",
        ),
        DeclareLaunchArgument(
            "cam_pos_x",
            default_value="0.0",
            description="",
        ),
        DeclareLaunchArgument(
            "cam_pos_y",
            default_value="0.0",
            description="",
        ),
        DeclareLaunchArgument(
            "cam_pos_z",
            default_value="0.0",
            description="",
        ),
        DeclareLaunchArgument(
            "cam_roll",
            default_value="0.0",
            description="",
        ),
        DeclareLaunchArgument(
            "cam_pitch",
            default_value="0.0",
            description="",
        ),
        DeclareLaunchArgument(
            "cam_yaw",
            default_value="0.0",
            description="",
        ),
        DeclareLaunchArgument(
            "use_node_composition",
            default_value="false",
            description="",
        ),
    ]

    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )