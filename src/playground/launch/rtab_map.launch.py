from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition, UnlessCondition
from launch_ros.actions import Node, PushRosNamespace
from launch.substitutions import PathJoinSubstitution, Command, FindExecutable
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue

def generate_launch_description():

    name = 'oak'

    # pkg = FindPackageShare('urdf_viewer')
    # xacro_file = PathJoinSubstitution([pkg, 'urdf', 'test.urdf.xacro'])
    # 
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
        'approx_sync':True,
        'approx_sync_max_interval': 0.05,
    }

    sync_remappings = [
        ("rgb/image", name + "/rgb/image_raw"),
        ("rgb/camera_info", name + "/rgb/camera_info"),
        ("depth/image", name + "/stereo/image_raw"),
    ]


    odom_parameters = {
        'subscribe_rgbd': True,

        'frame_id': 'oak-d-base-frame',
        'odom_frame_id': 'odom',

        'publish_tf': True,

        'approx_sync': True,
        # 'approx_sync_max_interval': 0.01,

        'wait_imu_to_init':True,
    }

    odom_remappings = [
        ("imu", name + "/imu/data"),   
        # ("rgb/image", name + "/rgb/image_raw"),
        # ("rgb/camera_info", name + "/rgb/camera_info"),
        # ("depth/image", name + "/stereo/image_raw"),
    ]


    slam_parameters = {
        'publish_tf': True,

        'frame_id': 'oak-d-base-frame',
        'odom_frame_id': 'odom',

        'subscribe_stereo': False,
        'subscribe_rgbd': True,
        'subscribe_depth': False,
        

        'subscribe_scan': False,
        'subscribe_scan_cloud': False, 

        'approx_sync': True,
        # 'approx_sync_max_interval': 0.01,

        'wait_imu_to_init':True,

        'queue_size': 100,
        'sync_queue_size': 100,
        'topic_queue_size': 100,

        'Reg/Strategy': '1',
        'Reg/Force3DoF': 'true',
        'Grid/RangeMin': '0.2',
        'Optimizer/GravitySigma': '0',
    }

    slam_remappings = [
        ("imu", name + "/imu/data"),   
    ]


    # viz_parameters = {
    #     'odom_frame_id': 'odom',

    #     'subscribe_stereo': False,

    #     'subscribe_rgbd': True,
    #     'subscribe_depth': False,


    #     'subscribe_scan': False,
    #     'subscribe_scan_cloud': True, 

    #     'approx_sync': True,
        
    #     'queue_size': 100,
    #     'sync_queue_size': 100,
    #     'topic_queue_size': 100,
    # }

    # viz_remappings = [
    #     ("rgb/image", name + "/rgb/image_raw"),
    #     ("rgb/camera_info", name + "/rgb/camera_info"),
    #     ("depth/image", name + "/stereo/image_raw"),
    # ]

    return LaunchDescription([

        # PushRosNamespace('rtab_map'),

        # Node(
        #     package='robot_state_publisher', executable='robot_state_publisher',
        #     name='robot_state_publisher',
        #     parameters=[robot_state_publisher_parameters],
        # ),

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
            parameters=[slam_parameters],
            remappings=slam_remappings,
            arguments=['-d']),

        # Node(
        #     package='rtabmap_viz', executable='rtabmap_viz', output='screen',
        #     name='rtabmap_viz',
        #     parameters=[viz_parameters],
        #     remappings=viz_remappings),
    ])
