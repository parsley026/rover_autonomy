from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition
from launch_ros.actions import PushRosNamespace, Node
from launch.substitutions import PathJoinSubstitution, Command, FindExecutable
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue
from launch.actions import GroupAction

def generate_launch_description():

    # pkg = FindPackageShare('urdf_viewer')
    # xacro_file = PathJoinSubstitution([pkg, 'urdf', 'test.urdf.xacro'])

    # robot_state_publisher_parameters = {
    #     'robot_description': ParameterValue(
    #         Command([
    #             FindExecutable(name='xacro'),
    #             ' ',
    #             xacro_file
    #         ]),
    #         value_type=str
    #     )
    # }
 

    sync_parameters = {
        'approx_sync': True,
        'approx_sync_max_interval': 0.1,
    }

    sync_remappings = [
        # ('/left/image_rect', '/zed/zed_node/left/image_rect_color'),
        # ('/left/camera_info', '/zed/zed_node/left/camera_info'),
        # ('/right/image_rect', '/zed/zed_node/right/image_rect_color'),
        # ('/right/camera_info', '/zed/zed_node/right/camera_info'),

         ('rgb/camera_info','/zed/zed_node/rgb/camera_info'),
         ('depth/image','/zed/zed_node/depth/depth_registered'),
         ('rgb/image','/zed/zed_node/rgb/image_rect_color'),
    ]


    odom_parameters = {
        'subscribe_rgbd': True,

        'frame_id': 'base_link',
        'odom_frame_id': 'odom',

        'publish_tf': True,

        'approx_sync': True,
        'approx_sync_max_interval': 0.1,
    }

    odom_remappings = [
        # ('/left/image_rect', '/zed/zed_node/left/image_rect_color'),
        # ('/left/camera_info', '/zed/zed_node/left/camera_info'),
        # ('/right/image_rect', '/zed/zed_node/right/image_rect_color'),
        # ('/right/camera_info', '/zed/zed_node/right/camera_info'),


        # ('/rgb/camera_info','/zed/zed_node/rgb/camera_info'),
        # ('/depth/image','/zed/zed_node/depth/depth_registered'),
        # ('/rgb/image','/zed/zed_node/rgb/image_rect_color')

        # ('/imu','/zed/zed_node/imu/data'),

        # ('/scan_cloud', '/ouster/points'),

    ]


    slam_parameters = {
        'publish_tf': True,

        'frame_id': 'base_link',
        'odom_frame_id': 'odom',

        'subscribe_stereo': False,

        'subscribe_rgb': False,
        'subscribe_rgbd': True,
        'subscribe_depth': False,
        

        'subscribe_scan': False,
        'subscribe_scan_cloud': True, 

        'approx_sync': True,
        'approx_sync_max_interval': 1,

        'odom_sensor_sync': True,

        'sync_queue_size': 100,
        'topic_queue_size': 100,

        'map_always_update': True,
    }

    slam_map_config = {
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

    # slam_loc_config = {
    #     'Mem/IncrementalMemory': 'False',
    #     'Mem/InitWMWithAllNodes': 'True',
    # }

    slam_remappings = [
        # ('/left/image_rect', '/zed/zed_node/left/image_rect_color'),
        # ('/left/camera_info', '/zed/zed_node/left/camera_info'),
        # ('/right/image_rect', '/zed/zed_node/right/image_rect_color'),
        # ('/right/camera_info', '/zed/zed_node/right/camera_info'),

        # ('/rgb/camera_info','/zed/zed_node/rgb/camera_info'),
        # ('/depth/image','/zed/zed_node/depth/depth_registered'),
        # ('/rgb/image','/zed/zed_node/rgb/image_rect_color')

        # ('/imu','/zed/zed_node/imu/data'),

        ('scan_cloud', '/ouster/points'),
    ]

    # pca_parameters = {
    #     'frame_id': 'base_link',
    # }

    # pca_remappings = [
    #     ('cloud1', '/ouster/points'),
    #     ('cloud2', '/zed/zed_node/point_cloud/cloud_registered'),
    # ]


    od_parameters = {
        'frame_id': 'base_link',
    }

    od_remappings = [
        ('cloud', '/zed/zed_node/point_cloud/cloud_registered'),
    ]

    # viz_parameters = {
    #     'odom_frame_id': 'odom',

    #     'subscribe_stereo': False,

    #     'subscribe_rgb': False,
    #     'subscribe_rgbd': True,
    #     'subscribe_depth': False,


    #     'subscribe_scan': False,
    #     'subscribe_scan_cloud': True, 

    #     'approx_sync': True,
    #     'approx_sync_max_interval': 0.1,

    #     'sync_queue_size': 100,
    #     'topic_queue_size': 100,
    # }

    # viz_remappings = [
    #     ('/scan_cloud', '/ouster/points'),
    # ]

    rtabmap_group = GroupAction([
        PushRosNamespace('rtabmap'),

    #    Node(
    #        package='robot_state_publisher', executable='robot_state_publisher',
    #        name='robot_state_publisher',
    #        parameters=[robot_state_publisher_parameters]),

        Node(
            package='rtabmap_sync', executable='rgbd_sync', output='screen',
            name='rtabmap_sync',
            parameters=[sync_parameters],
            remappings=sync_remappings),

        Node(
            package='rtabmap_odom', executable='rgbd_odometry', output='screen',
            name='rtabmap_odom',
            parameters=[odom_parameters],
            remappings=odom_remappings,
            arguments=["--ros-args", "--log-level", 'warn']),

        Node(
            package='rtabmap_slam', executable='rtabmap', output='screen',
            name='rtabmap_slam',
            parameters=[slam_parameters, slam_map_config],
            remappings=slam_remappings,
            arguments=['--delete_db_on_start']),

    #    Node(
    #        package='rtabmap_util', executable='point_cloud_aggregator', output='screen',
    #        name='rtabmap_util',
    #        parameters=[pca_parameters],
    #        remappings=pca_remappings),

       Node(
           package='rtabmap_util', executable='obstacles_detection', output='screen',
           name='rtabmap_util',
           parameters=[od_parameters],
           remappings=od_remappings),

    #     Node(
    #        package='rtabmap_slam', executable='rtabmap', output='screen',
    #        name='rtabmap_loc',
    #        parameters=[slam_parameters, slam_loc_config],
    #        remappings=slam_remappings),

    #    Node(
    #        package='rtabmap_viz', executable='rtabmap_viz', output='screen',
    #        name='rtabmap_viz',
    #        parameters=[viz_parameters],
    #        remappings=viz_remappings),

    ])

    return LaunchDescription([
        rtabmap_group
    ])
