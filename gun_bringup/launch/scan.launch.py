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
        # --- THE HARDWARE NODES ---
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            name='robot_state_publisher',
            parameters=[{'robot_description': robot_desc}],
            output='screen'
        ),
        Node(
            package='IMU_driver',
            executable='driver_node.py',
            name='scungun_imu',
            output='screen'
        ),
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
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_to_laser_tf',
            arguments=['0.0', '0.0', '0.0', '0.0', '0.0', '0.0', 'base_link', 'laser_link']
        ),
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='base_to_imu_tf',
            arguments=['-0.1146', '0.0', '-0.0445', '3.14159', '0.0', '0.0', 'base_link', 'imu_link']
        ),

        # --- THE OPEN-LOOP BRAIN ---
        Node(
            # CHANGE 'gun_bringup' TO WHATEVER PACKAGE YOU PUT THE SCRIPT IN
            package='gun_bringup', 
            executable='scungun_painter.py',
            name='scungun_painter',
            output='screen'
        )
    ])