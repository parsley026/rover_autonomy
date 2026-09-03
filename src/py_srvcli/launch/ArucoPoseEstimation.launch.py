from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='py_srvcli',
            executable='camera_node',
            name='hikvision_camera_node',
            output='screen',
            parameters=[
                {'rtsp_url': 'rtsp://admin:raptors12345@192.168.2.75:554/Streaming/Channels/101'},
                {'source': 'rtsp'}
            ]
        ),
        Node(
            package='py_srvcli',
            executable='aruco_node',
            name='aruco_position_node',
            output='screen'
        )
    ])