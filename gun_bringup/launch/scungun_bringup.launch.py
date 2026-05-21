import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    description_share = get_package_share_directory('IMU_description')
    urdf_file = os.path.join(description_share, 'urdf', 'IMU.urdf')

    with open(urdf_file, 'r') as infp:
        robot_desc = infp.read()

    return LaunchDescription([
        # 1. URDF Broadcaster
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{'robot_description': robot_desc}],
            output='screen'
        ),

        # 2. IMU Driver
        Node(
            package='IMU_driver',
            executable='driver_node.py',
            name='scungun_imu',
            output='screen'
        ),

        # 3. SLLidar A1M8 Node
        Node(
            package='sllidar_ros2',
            executable='sllidar_node',
            name='sllidar_node',
            parameters=[{
                'serial_port': '/dev/ttyUSB0',  # <-- Verify this port!
                'serial_baudrate': 115200,      # <-- A1M8 specific baudrate
                'frame_id': 'laser_link',
                'angle_compensate': True,
                'scan_mode': 'Standard'
            }],
            output='screen'
        ), # <--- ADDED COMMA HERE

        # Bridge 1: base_link to laser_link (Dead center, no offset)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_to_laser_tf',
            arguments=[
                '--x', '0.0', '--y', '0.0', '--z', '0.0',
                '--roll', '0.0', '--pitch', '0.0', '--yaw', '0.0',
                '--frame-id', 'base_link', '--child-frame-id', 'laser_link'
            ],
            output='screen'
        ), # <--- (You correctly had this comma already)

        # Bridge 2: base_link to imu_box_base (114.6mm back, 44.5mm down, flipped 180 on Z)
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_to_imu_tf',
            arguments=[
                '--x', '-0.1146', '--y', '0.0', '--z', '-0.0445',
                '--roll', '0.0', '--pitch', '0.0', '--yaw', '3.14159265',
                '--frame-id', 'base_link', '--child-frame-id', 'imu_box_base'
            ],
            output='screen'
        )
    ])