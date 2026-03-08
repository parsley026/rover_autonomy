from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, Command, FindExecutable, PathJoinSubstitution
from launch_ros.actions import LoadComposableNodes, Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.descriptions import ComposableNode
from launch_ros.parameter_descriptions import ParameterValue

def launch_setup(context, *args, **kwargs):

    xacro_file = LaunchConfiguration("xacro_file", default="").perform(context)

    robot_description = {
        'robot_description': ParameterValue(
            Command([
                FindExecutable(name='xacro'),
                ' ',
                xacro_file,
            ]),
            value_type=str
        )
    }

    namespace = LaunchConfiguration("namespace", default="")
    name      = LaunchConfiguration("name",      default="mounts").perform(context)

    use_node_composition = LaunchConfiguration("use_node_composition", default="false")

    return [
        Node(
            package='joint_state_publisher',
            executable='joint_state_publisher',
            name=name +'_joint_state_publisher',
            namespace=namespace,
            parameters=[robot_description]
        ),
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
                "sensor_mounts.urdf.xacro"
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
            default_value="mounts",
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
    