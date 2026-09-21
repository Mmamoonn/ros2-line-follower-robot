#!/usr/bin/env python3
"""
sensor_node.py

Role in the architecture:
    Publishes : /line_sensor   (std_msgs/Float32)
    Subscribes: /camera/image_raw (sensor_msgs/Image), bridged in from Gazebo

Why a camera instead of real IR sensors?
    In simulation there is no physical IR array to read from, so this node
    looks at a downward-facing camera image and treats it the way the real
    5-channel IR sensor array would: it splits the relevant strip of the
    image into 5 zones (far-left, left, center, right, far-right), decides
    whether each zone currently "sees" the dark line, and combines those
    5 yes/no readings into a single weighted error value.
"""

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from sensor_msgs.msg import Image
from std_msgs.msg import Float32
from rclpy.qos import qos_profile_sensor_data


class SensorNode(Node):
    def __init__(self):
        super().__init__('sensor_node')

        self.declare_parameter('camera_topic', '/camera/image_raw')
        self.declare_parameter('line_sensor_topic', '/line_sensor')
        self.declare_parameter('roi_top_fraction', 0.55)
        self.declare_parameter('binary_threshold', 90)
        self.declare_parameter('num_zones', 5)

        camera_topic = self.get_parameter('camera_topic').value
        line_sensor_topic = self.get_parameter('line_sensor_topic').value

        self.bridge = CvBridge()
        self.last_error = 0.0       # held when the line is briefly lost
        self.have_seen_line = False

        # Optimized: Using SensorDataQoS drops stale messages to prevent control loop latency
        self.publisher = self.create_publisher(
            Float32, line_sensor_topic, qos_profile_sensor_data)
        
        self.subscription = self.create_subscription(
            Image, camera_topic, self.image_callback, qos_profile_sensor_data)

        self.get_logger().info(
            f"sensor_node ready. Reading '{camera_topic}', "
            f"publishing line position to '{line_sensor_topic}'.")

    def image_callback(self, msg: Image):
        try:
            frame = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as exc:
            self.get_logger().warn(f"Could not convert image: {exc}")
            return

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape

        roi_top_fraction = self.get_parameter('roi_top_fraction').value
        threshold = self.get_parameter('binary_threshold').value
        num_zones = int(self.get_parameter('num_zones').value)

        roi_start_row = int(height * roi_top_fraction)
        roi = gray[roi_start_row:height, :]

        # Binary mask: pixels darker than threshold are "line"
        _, mask = cv2.threshold(roi, threshold, 255, cv2.THRESH_BINARY_INV)

        zone_width = width // num_zones
        active = []
        
        # Determine which zones "see" the line
        for i in range(num_zones):
            zone = mask[:, i * zone_width: (i + 1) * zone_width]
            fraction_dark = float(np.count_nonzero(zone)) / float(zone.size + 1e-6)
            active.append(1 if fraction_dark > 0.12 else 0)

        # Weighted-average algorithm
        half = num_zones // 2
        weights = list(range(-half, num_zones - half))

        active_count = sum(active)
        if active_count > 0:
            weighted_sum = sum(w * a for w, a in zip(weights, active))
            raw_error = weighted_sum / active_count
            # normalize so the output sits roughly in [-1, 1]
            error = raw_error / float(half if half > 0 else 1)
            self.last_error = error
            self.have_seen_line = True
        else:
            # Line lost: Keep steering the same direction it was last heading
            error = self.last_error if self.have_seen_line else 0.0

        out = Float32()
        out.data = float(error)
        self.publisher.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = SensorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
