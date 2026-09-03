from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def launch_setup(context, *args, **kwargs):
    params_file = LaunchConfiguration('params_file')
    namespace = LaunchConfiguration('namespace')

    use_sim_time = ParameterValue(
        LaunchConfiguration('use_sim_time'),
        value_type=bool
    )

    mapping_mode = str(LaunchConfiguration('mapping_mode').perform(context))
    camera_00_ns = LaunchConfiguration('camera_00_ns').perform(context)
    camera_01_ns = LaunchConfiguration('camera_01_ns').perform(context)
    lidar_ns = LaunchConfiguration('lidar_ns').perform(context)
    localization_ns = LaunchConfiguration('localization_ns').perform(context)

    mode_params = {}
    viz_remappings = [
        ('odom', f'/{localization_ns}/odometry/filtered'),
    ]

    if mapping_mode == '111':
        mode_params = {
            'subscribe_rgbd': True, 'rgbd_cameras': 0,
            'subscribe_scan_cloud': True, 'subscribe_depth': False,
            'Reg/Strategy': '2'
        }
        viz_remappings.extend([
            ('rgbd_images', 'rgbd_images'),
            ('scan_cloud', f'/{lidar_ns}/points')
        ])
    elif mapping_mode == '110':
        mode_params = {
            'subscribe_rgbd': True, 'rgbd_cameras': 1,
            'subscribe_scan_cloud': True, 'subscribe_depth': False,
            'Reg/Strategy': '2'
        }
        viz_remappings.extend([
            ('rgbd_image', f'/{camera_00_ns}/rgbd_image'),
            ('scan_cloud', f'/{lidar_ns}/points')
        ])
    elif mapping_mode == '101':
        mode_params = {
            'subscribe_rgbd': True, 'rgbd_cameras': 1,
            'subscribe_scan_cloud': True, 'subscribe_depth': False,
            'Reg/Strategy': '2'
        }
        viz_remappings.extend([
            ('rgbd_image', f'/{camera_01_ns}/rgbd_image'),
            ('scan_cloud', f'/{lidar_ns}/points')
        ])
    elif mapping_mode == '100':
        mode_params = {
            'subscribe_rgbd': False, 'subscribe_depth': False, 'subscribe_stereo': False,
            'subscribe_scan_cloud': True,
            'Reg/Strategy': '1', 'Icp/PointToPoint': 'true',
            'Grid/Sensor': '0'
        }
        viz_remappings.extend([
            ('scan_cloud', f'/{lidar_ns}/points')
        ])
    elif mapping_mode in ['011', '11', '9']:
        mode_params = {
            'subscribe_rgbd': True, 'rgbd_cameras': 0,
            'subscribe_scan_cloud': False, 'subscribe_depth': False,
            'Grid/FromDepth': 'true',
            'Reg/Strategy': '0',
            'Grid/Sensor': '1'
        }
        viz_remappings.extend([
            ('rgbd_images', 'rgbd_images')
        ])
    elif mapping_mode in ['010', '10', '8']:
        mode_params = {
            'subscribe_rgbd': True, 'rgbd_cameras': 1,
            'subscribe_scan_cloud': False, 'subscribe_depth': False,
            'Grid/FromDepth': 'true',
            'Reg/Strategy': '0',
            'Grid/Sensor': '1'
        }
        viz_remappings.extend([
            ('rgbd_image', f'/{camera_00_ns}/rgbd_image')
        ])
    elif mapping_mode in ['001', '1']:
        mode_params = {
            'subscribe_rgbd': True, 'rgbd_cameras': 1,
            'subscribe_scan_cloud': False, 'subscribe_depth': False,
            'Grid/FromDepth': 'true',
            'Reg/Strategy': '0',
            'Grid/Sensor': '1'
        }
        viz_remappings.extend([
            ('rgbd_image', f'/{camera_01_ns}/rgbd_image')
        ])

    return [
        Node(
            package='rtabmap_viz',
            executable='rtabmap_viz',
            name='rtabmap_viz',
            namespace=namespace,
            output='screen',
            parameters=[
                params_file,
                {
                    'use_sim_time': use_sim_time,
                    'rtabmap_node_name': LaunchConfiguration('rtabmap_node_name'),
                    'odometry_node_name': LaunchConfiguration('odometry_node_name'),
                },
                mode_params,
            ],
            remappings=viz_remappings,
        )
    ]


def generate_launch_description():
    pkg_share = FindPackageShare('rover_autonomy')
    default_params_file = PathJoinSubstitution([pkg_share, 'config', 'mapping', 'mapping.yaml'])

    return LaunchDescription([
        DeclareLaunchArgument('params_file', default_value=default_params_file, description=''),
        DeclareLaunchArgument('use_sim_time', default_value='false', description=''),
        DeclareLaunchArgument('namespace', default_value='mapping', description='Namespace for mapping'),
        DeclareLaunchArgument('rtabmap_node_name', default_value='rtabmap_slam', description='RTAB-Map node name used by rtabmap_viz.'),
        DeclareLaunchArgument('odometry_node_name', default_value='rgbd_odometry', description='Odometry node name used by rtabmap_viz.'),
        DeclareLaunchArgument('mapping_mode', default_value='110', description='SLAM Mode (Binary: LiDAR-Cam0-Cam1, e.g. 110)'),
        DeclareLaunchArgument('camera_00_ns', default_value='camera_00', description='Primary camera sensor namespace'),
        DeclareLaunchArgument('camera_01_ns', default_value='camera_01', description='Secondary camera sensor namespace'),
        DeclareLaunchArgument('lidar_ns', default_value='lidar_00', description='Lidar sensor namespace'),
        DeclareLaunchArgument('localization_ns', default_value='localization', description='Localization namespace'),
        OpaqueFunction(function=launch_setup)
    ])