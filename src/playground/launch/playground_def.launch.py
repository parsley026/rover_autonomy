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
    'qos_image': 2,
    'qos_camera_info': 2,
    
    'use_sim_time': False,             
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

    'qos': 1,
    'qos_image': 2,        
    'qos_camera_info': 2,
    'use_sim_time': False,

    'frame_id': 'base-link',
    'odom_frame_id': 'odom',
    'publish_tf': False,

    'approx_sync': True,
    'approx_sync_max_interval': 0.01,

    'publish_null_when_lost': False,
    'Odom/ResetCountdown': '1',

    'wait_imu_to_init': False,
}

camera_00_odom_remappings = [
]

# 

camera_01_params_file = '/home/rex/raptor_ws/src/playground/config/oak_d_pro.yaml'

camera_01_sync_parameters = {
    'approx_sync': True,
    'approx_sync_max_interval': 0.1,

    'qos': 1,
    'qos_image': 2,
    'qos_camera_info': 2,
    
    'use_sim_time': False,             
    'topic_queue_size': 50,          
    'sync_queue_size': 50, 
}

camera_01_sync_remappings = [
    ("rgb/camera_info", camera_01_namespace + "/rgb/camera_info"),
    ("rgb/image",       camera_01_namespace + "/rgb/image_raw/uncompressed"),

    ("depth/image",     camera_01_namespace + "/stereo/image_raw"),
]

# 

camera_01_odom_parameters = {
    'subscribe_rgbd': True,

    'qos': 1,
    'qos_image': 2,        
    'qos_camera_info': 2,
    'use_sim_time': False,

    'frame_id': 'base-link',
    'odom_frame_id': 'odom',
    'publish_tf': False,

    'approx_sync': True,
    'approx_sync_max_interval': 0.01,

    'publish_null_when_lost': False,
    'Odom/ResetCountdown': '1',

    'wait_imu_to_init': False,
}

camera_01_odom_remappings = [
]

# 

lidar_00_params_file = ''

lidar_00_odom_parameters = {
    'qos': 1,
    'qos_image': 2,        
    'qos_camera_info': 2,
    'use_sim_time': False,

    'frame_id': 'base-link',
    'odom_frame_id': 'odom',
    'publish_tf': False,

    'approx_sync': True,
    'approx_sync_max_interval': 0.01,

    'publish_null_when_lost': False,
    
    'subscribe_scan_cloud':True,

    'wait_imu_to_init': False,

    "queue_size_odom": "200",

    "Icp/MaxTranslation": "5",
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
    ("scan_cloud", "/lidar_00/points"),
    ("odom", "/lidar_00/odom"),
]

robot_localization_params_file_efk = '/home/rex/raptor_ws/src/playground/config/efk_filter.yaml'

robot_localization_params_file_ufk = '/home/rex/raptor_ws/src/playground/config/efk_filter.yaml'


slam_parameters = {
    'use_sim_time': False,
    'subscribe_depth': False,
    'subscribe_rgb': False,
    'subscribe_rgbd': True,          
    # 'rgbd_cameras': 2,               
    'subscribe_scan_cloud': True,    
    
    'frame_id': 'base-link',
    'map_frame_id': 'map',
    'odom_frame_id': 'odom',         
    'publish_tf': True,              
    'wait_for_transform': 0.2,       

    'map_always_update': True,


    'Rtabmap/DetectionRate': '10',
    'Rtabmap/TimeThr': '0',

    # 'Mem/IncrementalMemory': 'true', 
    # 'Mem/InitWMWithAllNodes': 'false', 
    # 'RGBD/OptimizeFromGraphEnd': 'false', 

    # 'RGBD/AngularUpdate': '0.05',    
    # 'RGBD/LinearUpdate': '0.05',     

    # 'RGBD/ProximityBySpace': 'true',     
    # 'Reg/Strategy': '2',                 
    # 'Reg/Force3DoF': 'false',            
    # 'RGBD/NeighborLinkRefining': 'true', 

    # 'Icp/PointToPlane': 'true',          
    # 'Icp/VoxelSize': '0.2',              
    # 'Icp/MaxCorrespondenceDistance': '1.0', 

    # 'RGBD/CreateOccupancyGrid': 'true',  
    # 'Grid/FromDepth': 'false',           
    # 'Grid/Sensor': '2',                  
    # 'Grid/3D': 'false',                  
    # 'Grid/RangeMax': '20.0',             
    # 'Grid/CellSize': '0.05',             
    # 'Grid/RayTracing': 'true',           

    #rtabmap
        'Rtabmap/DetectionRate': '10',
        'Rtabmap/TimeThr': '0',

        #mem
        'Mem/STMSize': '20',
        'Mem/IncrementalMemory': 'True',
        'Mem/InitWMWithAllNodes': 'False',

        #kp
        'Kp/MaxFeatures': '750',

        #rgbd
        'RGBD/NeighborLinkRefining': 'True',

        #reg
        'Reg/Strategy': '2',
        'Reg/Force3DoF': 'false',

        #vis
        
        #icp

        #stereo
        'Sterero/WinWidth': '15',
        'Sterero/WinHeight': '3',

        'Sterero/Iterations': '30',

        'Sterero/DenseStrategy': '0',

        #grid
        'Grid/Sensor': '2',

        'Grid/3D': 'True',

        'Grid/DepthDecimation': '4',

        'Grid/RangeMin': '0.5',
        'Grid/RangeMax': '5',

        'Grid/FootprintLength': '1.5',
        'Grid/FootprintWidth': '1.5',
        'Grid/FootprintHeight': '1.5',
        
        'Grid/MaxObstacleHeight': '0.2',

        'Grid/MinGroundHeight': '0.0',
        'Grid/MaxGroundHeight': '0.1',
        
        'Grid/MaxGroundAngle': '35',

        'Grid/FlatObstacleDetected': 'True',

        'Grid/FilteringRadious': '0.10',
        'Grid/NoiseFilteringMinNeighbor': '4',
    
        #global grid

        'GridGlobal/FootprintRadius': '0.75',
}

slam_remappings = [
    ("rgbd_image", f"/{camera_00_namespace}/rgbd_image"),
    ("scan_cloud", f"/{lidar_00_namespace}/points"),
    ("odom", "/odometry/filtered")
]

def launch_setup(context, *args, **kwargs):

    enable_camera_00 = LaunchConfiguration('enable_camera_00')
    enable_camera_01 = LaunchConfiguration('enable_camera_01')
    enable_lidar_00  = LaunchConfiguration('enable_lidar_00')

    mount_00_nodes = [
        Node(
            name='mount_state_publisher',
            namespace='mount_publisher',
            package="robot_state_publisher",
            executable="robot_state_publisher",
            parameters=[mount_00_description],
        ),
        Node(
            name='mount_joint_state_publisher',
            namespace='mount_publisher',
            package='joint_state_publisher',
            executable='joint_state_publisher',
            parameters=[mount_00_description]
        ),
    ]

    camera_00_nodes = [
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            name="camera_00_state_publisher",
            namespace=camera_00_namespace,
            parameters=[camera_00_description],
            condition=IfCondition(enable_camera_00)
        ),
        Node(
            package="depthai_ros_driver",
            executable="camera_node",
            name=camera_00_name,
            namespace=camera_00_namespace,
            parameters=[camera_00_params_file],
            condition=IfCondition(enable_camera_00)
        ),
        Node(
            package='rtabmap_sync',
            executable='rgbd_sync',
            name='rtabmap_sync',
            namespace=camera_00_namespace,
            parameters=[camera_00_sync_parameters],
            remappings=camera_00_sync_remappings,
            condition=IfCondition(enable_camera_00)
        ),
        Node(
            package='rtabmap_odom',
            executable='rgbd_odometry',
            name='rtabmap_odom',
            namespace=camera_00_namespace,
            parameters=[camera_00_odom_parameters],
            remappings=camera_00_odom_remappings,
            arguments=['--ros-args', '--log-level', 'fatal'],
            condition=IfCondition(enable_camera_00)
        ),
    ]

    camera_01_nodes = [
        Node(
            package="robot_state_publisher",
            executable="robot_state_publisher",
            name="camera_01_state_publisher",
            namespace=camera_01_namespace,
            parameters=[camera_01_description],
            condition=IfCondition(enable_camera_01)
        ),
        Node(
            package="depthai_ros_driver",
            executable="camera_node",
            name=camera_01_name,
            namespace=camera_01_namespace,
            parameters=[camera_01_params_file],
            condition=IfCondition(enable_camera_01)
        ),
        Node(
            package="image_transport",
            executable="republish",
            name="rgb_republish",
            namespace=camera_01_namespace,
            parameters=[{
                'in_transport':  'compressed',
                'out_transport': 'raw',
            }],
            remappings=[
                ("in/compressed", camera_01_namespace + "/rgb/image_raw/compressed"),
                ("out", camera_01_namespace + "/rgb/image_raw/uncompressed")
            ],
            condition=IfCondition(enable_camera_01)
        ),
        # Node(
        #     package="image_transport",
        #     executable="republish",
        #     name="stereo_republish",
        #     namespace=camera_01_namespace,
        #     parameters=[{
        #         'in_transport':  'compressed',
        #         'out_transport': 'raw',
        #     }],
        #     remappings=[
        #         ("in/compressed", camera_01_namespace + "/stereo/image_raw/compressed"),
        #         ("out", camera_01_namespace + "/stereo/image_raw/uncompressed")
        #     ],
        #     condition=IfCondition(enable_camera_01)
        # ),
        Node(
            package='rtabmap_sync',
            executable='rgbd_sync',
            name='rtabmap_sync',
            namespace=camera_01_namespace,
            parameters=[camera_01_sync_parameters],
            remappings=camera_01_sync_remappings,
            condition=IfCondition(enable_camera_01)
        ),
        # Node(
        #     package='rtabmap_odom',
        #     executable='rgbd_odometry',
        #     name='rtabmap_odom',
        #     namespace=camera_01_namespace,
        #     parameters=[camera_01_odom_parameters],
        #     remappings=camera_01_odom_remappings,
        #     arguments=['--ros-args', '--log-level', 'fatal'],
        #     condition=IfCondition(enable_camera_01)
        # ),
    ]

    lidar_00_nodes = [
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
                "ouster_ns": lidar_00_namespace,
            }.items(),
        ),
        Node(
            package='rtabmap_odom', 
            executable='icp_odometry',
            name='rtabmap_odom',
            namespace=lidar_00_namespace,
            parameters=[lidar_00_odom_parameters],
            remappings=lidar_00_odom_remappings,
            arguments=['--ros-args', '--log-level', 'fatal'],
            condition=IfCondition(enable_lidar_00)
        ),
    ]

    nodes = [
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            namespace='',
            output='screen',
            parameters=[robot_localization_params_file_efk]
        ),
        # Node(
        #     package='robot_localization',
        #     executable='ukf_node',
        #     name='ukf_filter_node',
        #     namespace='',
        #     output='screen',
        #     parameters=[robot_localization_params_file_ufk]
        # ),
        # Node(
        #     package='rtabmap_slam', 
        #     executable='rtabmap', 
        #     name='rtabmap_slam',
        #     namespace='mapping',
        #     output='screen',
        #     parameters=[slam_parameters],
        #     remappings=slam_remappings,
        #     arguments=['--delete_db_on_start']
        # ),
    ]

    return mount_00_nodes + camera_00_nodes + camera_01_nodes + lidar_00_nodes + nodes


def generate_launch_description():
    declared_arguments = [
        DeclareLaunchArgument('enable_camera_00', default_value='true'),
        DeclareLaunchArgument('enable_camera_01', default_value='true'),
        DeclareLaunchArgument('enable_lidar_00',  default_value='true'),
    ]

    return LaunchDescription(
        declared_arguments + [OpaqueFunction(function=launch_setup)]
    )
    