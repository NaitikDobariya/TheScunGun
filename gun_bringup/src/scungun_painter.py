#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu, LaserScan, PointCloud2
from tf2_ros import TransformBroadcaster
from geometry_msgs.msg import TransformStamped
import sensor_msgs_py.point_cloud2 as pc2
from std_msgs.msg import Header

import numpy as np
import open3d as o3d
from scipy.spatial.transform import Rotation as R

class ScunGunPro(Node):
    def __init__(self):
        super().__init__('scungun_painter')

        # --- STATE (Position, Velocity, Orientation) ---
        self.pos = np.array([0.0, 0.0, 0.0]) 
        self.vel = np.array([0.0, 0.0, 0.0])
        self.q = np.array([0.0, 0.0, 0.0, 1.0]) # x, y, z, w
        self.last_imu_time = self.get_clock().now()

        # --- THE GLOBAL 3D MAP ---
        self.global_map = o3d.geometry.PointCloud()
        self.voxel_size = 0.04 # 4cm resolution for a good balance of detail/speed
        self.icp_threshold = 0.5 

        self.tf_broadcaster = TransformBroadcaster(self)

        # --- PUBS & SUBS ---
        self.imu_sub = self.create_subscription(Imu, '/imu/data', self.imu_callback, 100)
        self.scan_sub = self.create_subscription(LaserScan, '/scan', self.scan_callback, 10)
        self.pc_pub = self.create_publisher(PointCloud2, '/scungun_cloud', 10)

        self.get_logger().info("ScunGun PRO: Closed-Loop 3D Mapping Active!")

    def imu_callback(self, msg):
        now = self.get_clock().now()
        dt = (now - self.last_imu_time).nanoseconds / 1e9
        self.last_imu_time = now

        if dt <= 0 or dt > 0.1: return

        # 1. Update Orientation from BNO085 (The source of our 3D tilt)
        self.q = np.array([msg.orientation.x, msg.orientation.y, msg.orientation.z, msg.orientation.w])

        # 2. Dead Reckoning (The "Seed" for ICP)
        accel = np.array([msg.linear_acceleration.x, msg.linear_acceleration.y, msg.linear_acceleration.z])
        accel[np.abs(accel) < 0.15] = 0.0 # Clean noise

        # Update Velocity and Position with Virtual Friction
        self.vel = (self.vel + accel * dt) * 0.92 
        self.pos = self.pos + (self.vel * dt) # Fix: standard assignment to avoid Read-Only error

        # 3. Publish TF (map -> base_link)
        self.publish_tf(msg.header.stamp)

    def scan_callback(self, msg):
        # 1. Project 2D Scan into 3D Space (Local Frame)
        angles = np.linspace(msg.angle_min, msg.angle_max, len(msg.ranges))
        ranges = np.array(msg.ranges)
        valid = (ranges > msg.range_min) & (ranges < msg.range_max)
        
        x = ranges[valid] * np.cos(angles[valid])
        y = ranges[valid] * np.sin(angles[valid])
        z = np.zeros_like(x)
        local_points = np.vstack((x, y, z)).T

        # Create Open3D cloud for the new scan
        current_scan = o3d.geometry.PointCloud()
        current_scan.points = o3d.utility.Vector3dVector(local_points)
        current_scan = current_scan.voxel_down_sample(self.voxel_size)

        # 2. Create the "Initial Guess" Transformation (Tilt + Position)
        # This is where the 3D 'painting' happens
        T_guess = np.eye(4)
        T_guess[:3, :3] = R.from_quat(self.q).as_matrix()
        T_guess[:3, 3] = self.pos

        # 3. THE CLOSED-LOOP (ICP)
        if len(self.global_map.points) == 0:
            # First scan creates the world
            current_scan.transform(T_guess)
            self.global_map = current_scan
            self.publish_cloud(msg.header.stamp)
            return

        # Snap the current tilted scan to the existing 3D map
        reg = o3d.pipelines.registration.registration_icp(
            current_scan, self.global_map, self.icp_threshold, T_guess,
            o3d.pipelines.registration.TransformationEstimationPointToPoint()
        )

        # 4. Feedback & Mapping
        if reg.fitness > 0.4: # Require 40% overlap for a "lock"
            # Snap our internal position to the ICP result
            # Fix: Use np.copy to prevent Read-Only buffer errors
            self.pos = np.copy(reg.transformation[:3, 3])
            
            # Merge the new tilted points into our permanent 3D world
            current_scan.transform(reg.transformation)
            self.global_map += current_scan
            
            # Clean up the map to prevent memory bloat
            self.global_map = self.global_map.voxel_down_sample(self.voxel_size)
            
            # Show the world
            self.publish_cloud(msg.header.stamp)
        else:
            self.get_logger().warn("ICP Lock Lost! Relying on IMU tilt.")

    def publish_tf(self, stamp):
        t = TransformStamped()
        t.header.stamp = stamp
        t.header.frame_id = 'map'
        t.child_frame_id = 'base_link'
        t.transform.translation.x, t.transform.translation.y, t.transform.translation.z = self.pos
        t.transform.rotation.x, t.transform.rotation.y, t.transform.rotation.z, t.transform.rotation.w = self.q
        self.tf_broadcaster.sendTransform(t)

    def publish_cloud(self, stamp):
        points = np.asarray(self.global_map.points)
        header = Header(stamp=stamp, frame_id='map')
        ros_cloud = pc2.create_cloud_xyz32(header, points)
        self.pc_pub.publish(ros_cloud)

def main():
    rclpy.init()
    node = ScunGunPro()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()