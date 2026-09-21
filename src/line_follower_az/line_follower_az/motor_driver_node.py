#!/usr/bin/env python3
"""
motor_driver_node.py

Role in the architecture:
    Publishes : /wheel_velocity (std_msgs/Float32MultiArray, [left, right] rad/s)
    Subscribes: /cmd_vel        (geometry_msgs/Twist)
"""

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray
from rcl_interfaces.msg import SetParametersResult


class MotorDriverNode(Node):
    def __init__(self):
        super().__init__('motor_driver_node')

        self.declare_parameter('wheel_radius', 0.033)
        self.declare_parameter('wheel_separation', 0.15)
        self.declare_parameter('max_wheel_speed', 12.0)
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')
        self.declare_parameter('wheel_velocity_topic', '/wheel_velocity')

        # Cache structural parameters
        self.wheel_radius = self.get_parameter('wheel_radius').value
        self.wheel_separation = self.get_parameter('wheel_separation').value
        self.max_wheel_speed = self.get_parameter('max_wheel_speed').value

        cmd_vel_topic = self.get_parameter('cmd_vel_topic').value
        wheel_velocity_topic = self.get_parameter('wheel_velocity_topic').value

        self.add_on_set_parameters_callback(self.parameters_callback)

        # REVERTED to 10 to ensure monitor_node can subscribe to this data
        self.publisher = self.create_publisher(
            Float32MultiArray, wheel_velocity_topic, 10)
        
        # REVERTED to 10 to match the reliable Twist messages coming from pid_controller_node
        self.subscription = self.create_subscription(
            Twist, cmd_vel_topic, self.cmd_vel_callback, 10)

        self.get_logger().info(
            f"motor_driver_node ready. Converting '{cmd_vel_topic}' into "
            f"left/right wheel speeds on '{wheel_velocity_topic}'.")

    def parameters_callback(self, params):
        for param in params:
            if hasattr(self, param.name):
                setattr(self, param.name, param.value)
        return SetParametersResult(successful=True)

    def cmd_vel_callback(self, msg: Twist):
        v = msg.linear.x
        w = msg.angular.z

        # Standard differential-drive kinematics
        v_left = (v - w * self.wheel_separation / 2.0) / self.wheel_radius
        v_right = (v + w * self.wheel_separation / 2.0) / self.wheel_radius

        v_left = max(-self.max_wheel_speed, min(self.max_wheel_speed, v_left))
        v_right = max(-self.max_wheel_speed, min(self.max_wheel_speed, v_right))

        out = Float32MultiArray()
        out.data = [float(v_left), float(v_right)]
        self.publisher.publish(out)


def main(args=None):
    rclpy.init(args=args)
    node = MotorDriverNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
