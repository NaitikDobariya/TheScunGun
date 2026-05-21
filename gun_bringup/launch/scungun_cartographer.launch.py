import os
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # 1. Get Paths
    description_share = get_package_share_directory('IMU_description')
    bringup_share = get_package_share_directory('gun_bringup')
    
    urdf_file = os.path.join(description_share, 'urdf', 'IMU.urdf')
    lua_config_dir = os.path.join(bringup_share, 'config')

    with open(urdf_file, 'r') as infp:
        robot_desc = infp.read()

    return LaunchDescription([
        # --- THE HARDWARE NODES ---

        # robot_state_publisher (The "Skeleton")
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{'robot_description': robot_desc}],
            output='screen'
        ),

        # IMU Driver (The "Ears")
        Node(
            package='IMU_driver',
            executable='driver_node.py',
            name='scungun_imu',
            output='screen'
        ),

        # SLLidar A1M8 (The "Eyes")
        Node(
            package='sllidar_ros2',
            executable='sllidar_node',
            name='sllidar_node',
            parameters=[{
                'serial_port': '/dev/ttyUSB0',  
                'serial_baudrate': 115200,      
                'frame_id': 'laser_link',
                'angle_compensate': True,
                'scan_mode': 'Standard'
            }],
            output='screen'
        ),

        # --- THE TRANSFORMS (The "Joints") ---

        # Bridge 1: Center of gun to Laser
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_to_laser_tf',
            arguments=['0.0', '0.0', '0.0', '0.0', '0.0', '0.0', 'base_link', 'laser_link']
        ),

        # Bridge 2: Center of gun to IMU (Flipped 180 on Yaw/Z)
        # Note: We use 'imu_link' here because that's what your driver_node.py publishes
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_to_imu_tf',
            arguments=['-0.1146', '0.0', '-0.0445', '3.14159', '0.0', '0.0', 'base_link', 'imu_link']
        ),

        # --- THE SLAM (The "Brain") ---

        # Cartographer Node
        Node(
            package='cartographer_ros',
            executable='cartographer_node',
            name='cartographer_node',
            arguments=[
                '-configuration_directory', lua_config_dir,
                '-configuration_basename', 'scungun_3d.lua'
            ],
            remappings=[('/imu', '/imu/data')],
            output='screen'
        ),

        # Map Grid Node
        Node(
            package='cartographer_ros',
            executable='cartographer_occupancy_grid_node',
            name='cartographer_occupancy_grid_node',
            arguments=['-resolution', '0.05'],
        )
    ])