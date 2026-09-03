from launch import LaunchDescription
from launch.conditions import UnlessCondition
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration, Command, FindExecutable, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

def launch_setup(context, *args, **kwargs):
    urdf_package   = LaunchConfiguration('urdf_package').perform(context)
    urdf_file      = LaunchConfiguration('urdf_file').perform(context)
    
    description_ns = LaunchConfiguration('description_ns')

    use_sim_time = ParameterValue(
        LaunchConfiguration('use_sim_time'),
        value_type=bool
    )

    mount_description = {
        'robot_description': ParameterValue(
            Command([
                FindExecutable(name='xacro'),
                ' "',
                PathJoinSubstitution([
                    FindPackageShare(urdf_package),
                    'urdf',
                    urdf_file
                ]),
                '" module_position_front:=',
                LaunchConfiguration('module_position_front'),
                ' module_position_back:=',
                LaunchConfiguration('module_position_back'),
            ]),
            value_type=str
        )
    }

    return [
        Node(
            name='mount_state_publisher',
            namespace=description_ns,     # 2. Replaced the duplicate namespace kwargs
            package="robot_state_publisher",
            executable="robot_state_publisher",
            parameters=[mount_description, {'use_sim_time': use_sim_time}],
            remappings=[
                ('tf', '/tf'),
                ('tf_static', '/tf_static')
            ],
            condition=UnlessCondition(LaunchConfiguration('use_sim_time'))
        ),
        Node(
            name='mount_joint_state_publisher',
            namespace=description_ns,     # 3. Replaced the duplicate namespace kwargs
            package='joint_state_publisher',
            executable='joint_state_publisher',
            parameters=[mount_description, {'use_sim_time': use_sim_time}],
            remappings=[
                ('tf', '/tf'),
                ('tf_static', '/tf_static')
            ],
            condition=UnlessCondition(LaunchConfiguration('use_sim_time'))
        ),
    ]

def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('urdf_package', default_value='rover_autonomy'),
        DeclareLaunchArgument('urdf_file',    default_value='sensor_mounts.urdf.xacro'),

        DeclareLaunchArgument('description_ns',   default_value='autonomy_submodule', description=''),
        DeclareLaunchArgument('module_position_front',  default_value='true', description='Mount module in front'),
        DeclareLaunchArgument('module_position_back',   default_value='false', description='Mount module in back'),

        DeclareLaunchArgument('use_sim_time', default_value='false', description=''),
        OpaqueFunction(function=launch_setup)
    ])