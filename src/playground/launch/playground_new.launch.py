from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, IncludeLaunchDescription, TimerAction
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, Command, FindExecutable, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node, ComposableNodeContainer, LoadComposableNodes
from launch_ros.descriptions import ComposableNode
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

mount_00_description = {
        'robot_description': ParameterValue(
            Command([
                FindExecutable(name='xacro'),
                ' ',
                '/home/rex/raptor_ws/src/playground/urdf/sensor_mounts.urdf.xacro',
            ]),
            value_type=str
        )
    }

camera_00_namespace = 'camera_00'

camera_00_name = 'camera_00'

camera_00_base_frame = 'camera-00-link'

camera_00_parent_frame = 'sensor-mount-00-link'

camera_00_description = {
        'robot_description': ParameterValue(
            Command([
                FindExecutable(name='xacro'),
                ' ',
                '/home/rex/raptor_ws/src/playground/urdf/depthai_camera_description.urdf.xacro',
                f" camera_name:={camera_00_name}",
                # f" camera_model:={camera_model}",
                f" base_frame:={camera_00_base_frame}",
                f" parent_frame:={camera_00_parent_frame}",
                # f" cam_pos_x:={cam_pos_x}",
                # f" cam_pos_y:={cam_pos_y}",
                # f" cam_pos_z:={cam_pos_z}",
                # f" cam_roll:={cam_roll}",
                # f" cam_pitch:={cam_pitch}",
                # f" cam_yaw:={cam_yaw}",
            ]),
            value_type=str
        )
    }

camera_01_namespace = 'camera_01'

camera_01_name = 'camera_01'

camera_01_base_frame = 'camera-01-link'

camera_01_parent_frame = 'sensor-mount-01-link'

camera_01_description = {
        'robot_description': ParameterValue(
            Command([
                FindExecutable(name='xacro'),
                ' ',
                '/home/rex/raptor_ws/src/playground/urdf/depthai_camera_description.urdf.xacro',
                f" camera_name:={camera_01_name}",
                # f" camera_model:={camera_model}",
                f" base_frame:={camera_01_base_frame}",
                f" parent_frame:={camera_01_parent_frame}",
                # f" cam_pos_x:={cam_pos_x}",
                # f" cam_pos_y:={cam_pos_y}",
                # f" cam_pos_z:={cam_pos_z}",
                # f" cam_roll:={cam_roll}",
                # f" cam_pitch:={cam_pitch}",
                # f" cam_yaw:={cam_yaw}",
            ]),
            value_type=str
        )
    }

lidar_00_namespace  = 'lidar_00'

lidar_00_name = 'lidar_00'

camera_00_params_file = '/home/rex/raptor_ws/src/playground/config/oak_d.yaml'

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

camera_00_odom_parameters = {
    'subscribe_rgbd': True,

    'frame_id': 'base-link',
    'odom_frame_id': 'odom',

    'publish_tf': True,

    'approx_sync': True,
    'approx_sync_max_interval': 0.01,
}

camera_00_odom_remappings = [
]

# 

camera_01_params_file = '/home/rex/raptor_ws/src/playground/config/oak_d_pro.yaml'

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

lidar_00_params_file = ''

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

    ("/scan_cloud", lidar_00_namespace + lidar_00_name + "/points"),
]

robot_localization_parameters = {}

slam_parameters = {}

slam_remappings = []

def launch_setup(context, *args, **kwargs):

    enable_camera_00 = LaunchConfiguration('enable_camera_00')
    enable_camera_01 = LaunchConfiguration('enable_camera_01')
    enable_lidar_00  = LaunchConfiguration('enable_lidar_00')

    camera_00_nodes = [
        ComposableNode(
            package="robot_state_publisher",
            plugin="robot_state_publisher::RobotStatePublisher",
            name=camera_00_name,
            namespace=camera_00_namespace,
            parameters=[camera_00_description],
        ),
        ComposableNode(
            package="depthai_ros_driver",
            plugin="depthai_ros_driver::Camera",
            name=camera_00_name,
            namespace=camera_00_namespace,
            parameters=[camera_00_params_file],
        ),
        # ComposableNode(
        #     package='rtabmap_sync',
        #     plugin='rtabmap_sync::RGBDSync',
        #     name='rtabmap_sync',
        #     namespace=camera_00_namespace,
        #     parameters=[camera_00_sync_parameters],
        #     remappings=camera_00_sync_remappings
        # ),
        # ComposableNode(
        #     package='rtabmap_odom',
        #     plugin='rtabmap_odom::RGBDOdometry',
        #     name='rtabmap_odom',
        #     namespace=camera_00_namespace,
        #     parameters=[camera_00_odom_parameters],
        #     remappings=camera_00_odom_remappings,
        #     extra_arguments=[{'--ros-args': '', '--log-level': 'warn'}]
        # ),
    ]

    camera_01_nodes = [
        ComposableNode(
            package="robot_state_publisher",
            plugin="robot_state_publisher::RobotStatePublisher",
            name=camera_01_name,
            namespace=camera_01_namespace,
            parameters=[camera_01_description],
        ),
        ComposableNode(
            package="depthai_ros_driver",
            plugin="depthai_ros_driver::Camera",
            name=camera_01_name,
            namespace=camera_01_namespace,
            parameters=[camera_01_params_file],
        ),
        # ComposableNode(
        #     package='rtabmap_sync',
        #     plugin='rtabmap_sync::RGBDSync',
        #     name='rtabmap_sync',
        #     namespace=camera_01_namespace,
        #     parameters=[camera_01_sync_parameters],
        #     remappings=camera_01_sync_remappings
        # ),
        # ComposableNode(
        #     package='rtabmap_odom',
        #     plugin='rtabmap_odom::RGBDOdometry',
        #     name='rtabmap_odom',
        #     namespace='',
        #     parameters=[camera_01_odom_parameters],
        #     remappings=camera_01_odom_remappings,
        #     extra_arguments=[{'--ros-args': '', '--log-level': 'warn'}]
        # ),
    ]

    # lidar_00_nodes = [
    #     ComposableNode(
    #         package='rtabmap_odom', 
    #         plugin='rtabmap_odom::ICPOdometry',
    #         name='rtabmap_odom',
    #         namespace='',
    #         parameters=[lidar_00_odom_parameters],
    #         remappings=lidar_00_odom_remappings,
    #         extra_arguments=[{'--ros-args': '', '--log-level': 'warn'}]
    #     ),
    #]

    return [
        Node(
            name='mount_state_publisher',
            namespace='',
            package="robot_state_publisher",
            executable="robot_state_publisher",
            parameters=[mount_00_description],
        ),
        Node(
            name='mount_state_publisher',
            namespace='',
            package='joint_state_publisher',
            executable='joint_state_publisher',
            parameters=[mount_00_description]
        ),

        # ComposableNodeContainer(
        #     name='camera_00_container',
        #     namespace='',
        #     package='rclcpp_components',
        #     executable='component_container_mt',
        #     composable_node_descriptions=camera_00_nodes,
        #     output='screen',
        #     condition=IfCondition(enable_camera_00)
        # ),

        ComposableNodeContainer(
            name='camera_01_container',
            namespace='',
            package='rclcpp_components',
            executable='component_container_mt',
            composable_node_descriptions=camera_01_nodes,
            output='screen',
            condition=IfCondition(enable_camera_01)
        ),
        Node(
            package="image_transport",
            executable="republish",
            name="rgb_republish",
            namespace=camera_01_namespace,
            arguments=['compressed', 'raw'],
            remappings=[
                ("in/compressed", camera_01_namespace + "/rgb/image_raw/compressed"),
                ("out", camera_01_namespace + "/rgb/image_raw/uncompressed")
            ]
        ),
        Node(
            package="image_transport",
            executable="republish",
            name="stereo_republish",
            namespace=camera_01_namespace,
            arguments=['compressed', 'raw'],
            remappings=[
                ("in/compressed", camera_01_namespace + "/stereo/image_raw/compressed"),
                ("out", camera_01_namespace + "/stereo/image_raw/uncompressed")
            ]
        ),
        # ComposableNodeContainer(
        #     name='lidar_00_container',
        #     namespace='',
        #     package='rclcpp_components',
        #     executable='component_container_mt',
        #     composable_node_descriptions=lidar_00_nodes,
        #     output='screen',
        #     condition=IfCondition(enable_lidar_00)
        # ),

        # Node(
        #     package='robot_localization',
        #     executable='ekf_node',
        #     name='ekf_filter_node',
        #     namespace='',J
        #     output='screen',
        #     parameters=[robot_localization_parameters]
        # ),

        # Node(
        #     package='rtabmap_slam', 
        #     executable='rtabmap', 
        #     name='rtabmap_slam',
        #     namespace='',
        #     output='screen',
        #     parameters=[slam_parameters],
        #     remappings=slam_remappings,
        #     arguments=['--delete_db_on_start']
        # ),
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
    