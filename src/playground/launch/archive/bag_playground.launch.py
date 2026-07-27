from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, Command, FindExecutable, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node, ComposableNodeContainer, LoadComposableNodes
from launch_ros.descriptions import ComposableNode
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

camera_00_namespace = 'oak_d_pro/oak_d_pro'

camera_01_namespace = 'oak_d_pro/oak_d_pro'

lidar_00_namespace  = 'ouster_os'

camera_00_sync_parameters = {
    'approx_sync': True,
    'approx_sync_max_interval': 0.1,

    'qos': 1,
    'qos_camera_info': 1,
    
    'use_sim_time': True,             
    'topic_queue_size': 50,          
    'sync_queue_size': 50, 
}

camera_00_sync_remappings = [
    ("rgb/camera_info", camera_00_namespace + "/rgb/camera_info"),
    ("rgb/image",       camera_00_namespace + "/rgb/image_raw"),

    ("depth/image",     camera_00_namespace + "/stereo/image_raw"),
]

# 

camera_00_odom_parameters = {}

camera_00_odom_remappings = [
    ("/imu", "/imu/data"),
]

# 

camera_01_sync_parameters = {
    'approx_sync': True,
    'approx_sync_max_interval': 0.1,

    'qos': 1,
    'qos_camera_info': 1,

    'use_sim_time': True,             
    'topic_queue_size': 50,          
    'sync_queue_size': 50,            
}

camera_01_sync_remappings = [
    ("rgb/camera_info", camera_01_namespace + "/rgb/camera_info"),
    ("rgb/image",       camera_01_namespace + "/rgb/image_raw"),
    
    ("depth/image",     camera_01_namespace + "/stereo/image_raw"),
]

# 

camera_01_odom_parameters = {}

camera_01_odom_remappings = [
    ("/imu", "/imu/data"),
]

# 

lidar_00_odom_parameters = {
    'subscribe_rgbd': True,

    'frame_id': 'base-link',
    'odom_frame_id': 'odom',

    'publish_tf': True,

    # 'approx_sync': True,
    # 'approx_sync_max_interval': 0.01,

    # 'wait_imu_to_init':True,

    'use_sim_time': True,

    "Icp/MaxTranslation": "5",
    "queue_size_odom": "100",
    "ground_normals_up": "true",
    "Icp/VoxelSize": "0.4",
    "Icp/MaxCorrespondenceDistance": "4.0",
    "Icp/PointToPlaneK": "20",
    "Odom/Strategy": "0",
    "OdomF2M/ScanSubtractRadius": "0.5",
    "OdomLOAM/Sensor": "2",
    "OdomLOAM/Resolution": "0.4"
}

lidar_00_odom_remappings = [
    # ("/imu", "/imu/data"),

    ("/scan_cloud", lidar_00_namespace + "/points"),
]

robot_localization_parameters = {}

slam_parameters = {}

slam_remappings = []

def launch_setup(context, *args, **kwargs):

    enable_camera_00 = LaunchConfiguration('enable_camera_00')
    enable_camera_01 = LaunchConfiguration('enable_camera_01')
    enable_lidar_00  = LaunchConfiguration('enable_lidar_00')

    # camera_00_nodes = [
    #     ComposableNode(
    #         package='rtabmap_sync',
    #         plugin='rtabmap_sync::RGBDSync',
    #         name='rtabmap_sync',
    #         namespace='',
    #         parameters=[camera_00_sync_parameters],
    #         remappings=camera_00_sync_remappings
    #     ),
    #     ComposableNode(
    #         package='rtabmap_odom',
    #         plugin='rtabmap_odom::RGBDOdometry',
    #         name='rtabmap_odom',
    #         namespace='',
    #         parameters=[camera_00_odom_parameters],
    #         remappings=camera_00_odom_remappings,
    #         extra_arguments=[{'--ros-args': '', '--log-level': 'warn'}]
    #     ),
    # ]

    # camera_01_nodes = [
    #     ComposableNode(
    #         package='rtabmap_sync',
    #         plugin='rtabmap_sync::RGBDSync',
    #         name='rtabmap_sync',
    #         namespace='',
    #         parameters=[camera_01_sync_parameters],
    #         remappings=camera_01_sync_remappings
    #     ),
    #     ComposableNode(
    #         package='rtabmap_odom',
    #         plugin='rtabmap_odom::RGBDOdometry',
    #         name='rtabmap_odom',
    #         namespace='',
    #         parameters=[camera_01_odom_parameters],
    #         remappings=camera_01_odom_remappings,
    #         extra_arguments=[{'--ros-args': '', '--log-level': 'warn'}]
    #     ),
    # ]

    lidar_00_nodes = [
        ComposableNode(
            package='rtabmap_odom', 
            plugin='rtabmap_odom::ICPOdometry',
            name='rtabmap_odom',
            namespace='',
            parameters=[lidar_00_odom_parameters],
            remappings=lidar_00_odom_remappings,
            extra_arguments=[{'--ros-args': '', '--log-level': 'warn'}]
        ),
    ]

    return [
        # ComposableNodeContainer(
        #     name='camera_00_container',
        #     namespace='',
        #     package='rclcpp_components',
        #     executable='component_container_mt',
        #     composable_node_descriptions=camera_00_nodes,
        #     output='screen',
        #     condition=IfCondition(enable_camera_00)
        # ),

        # ComposableNodeContainer(
        #     name='camera_01_container',
        #     namespace='',
        #     package='rclcpp_components',
        #     executable='component_container_mt',
        #     composable_node_descriptions=camera_01_nodes,
        #     output='screen',
        #     condition=IfCondition(enable_camera_01)
        # ),
        
        ComposableNodeContainer(
            name='lidar_00_container',
            namespace='',
            package='rclcpp_components',
            executable='component_container_mt',
            composable_node_descriptions=lidar_00_nodes,
            output='screen',
            condition=IfCondition(enable_lidar_00)
        ),

        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            namespace='',
            output='screen',
            parameters=[robot_localization_parameters]
        ),

        Node(
            package='rtabmap_slam', 
            executable='rtabmap', 
            name='rtabmap_slam',
            namespace='',
            output='screen',
            parameters=[slam_parameters],
            remappings=slam_remappings,
            arguments=['--delete_db_on_start']
        ),
    ]


def generate_launch_description():
    declared_arguments = [
        DeclareLaunchArgument('enable_camera_00', default_value='true'),
        DeclareLaunchArgument('enable_camera_01', default_value='true'),
        DeclareLaunchArgument('enable_lidar_00',  default_value='true'),
    ]

    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )
    