#!/usr/bin/env python3
"""
pid_controller_node.py

Role in the architecture:
    Publishes : /cmd_vel        (geometry_msgs/Twist)
    Subscribes: /line_sensor    (std_msgs/Float32)
"""

import time
import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node
from std_msgs.msg import Float32
from rclpy.qos import qos_profile_sensor_data
from rcl_interfaces.msg import SetParametersResult


class PIDControllerNode(Node):
    def __init__(self):
        super().__init__('pid_controller_node')

        self.declare_parameter('Kp', 0.8)
        self.declare_parameter('Ki', 0.02)
        self.declare_parameter('Kd', 0.15)
        self.declare_parameter('base_linear_speed', 0.12)
        self.declare_parameter('min_linear_speed', 0.04)
        self.declare_parameter('max_angular_z', 2.5)
        self.declare_parameter('integral_clamp', 1.0)
        self.declare_parameter('error_topic', '/line_sensor')
        self.declare_parameter('cmd_vel_topic', '/cmd_vel')

        # Cache parameters to avoid expensive lookups in the control loop
        self.Kp = self.get_parameter('Kp').value
        self.Ki = self.get_parameter('Ki').value
        self.Kd = self.get_parameter('Kd').value
        self.base_linear_speed = self.get_parameter('base_linear_speed').value
        self.min_linear_speed = self.get_parameter('min_linear_speed').value
        self.max_angular_z = self.get_parameter('max_angular_z').value
        self.integral_clamp = self.get_parameter('integral_clamp').value

        error_topic = self.get_parameter('error_topic').value
        cmd_vel_topic = self.get_parameter('cmd_vel_topic').value

        self._integral = 0.0
        self._prev_error = 0.0
        self._prev_time = time.monotonic()

        # Register callback for dynamic parameter updates (Live Tuning)
        self.add_on_set_parameters_callback(self.parameters_callback)

        # Publisher set to 10 (Reliable) to communicate with Gazebo
        self.publisher = self.create_publisher(
            Twist, cmd_vel_topic, 10)
        
        # Sensor subscription remains Best Effort to prevent input lag
        self.subscription = self.create_subscription(
            Float32, error_topic, self.error_callback, qos_profile_sensor_data)

        self.get_logger().info(
            f"pid_controller_node ready. Listening on '{error_topic}', "
            f"driving '{cmd_vel_topic}'. Tune live via rqt or CLI.")

    def parameters_callback(self, params):
        for param in params:
            if hasattr(self, param.name):
                setattr(self, param.name, param.value)
                self.get_logger().info(f"Updated {param.name} to {param.value}")
        return SetParametersResult(successful=True)

    def error_callback(self, msg: Float32):
        error = float(msg.data)

        now = time.monotonic()
        dt = now - self._prev_time
        self._prev_time = now
        if dt <= 0.0:
            dt = 1e-3  

        # --- P term ---
        p_term = self.Kp * error

        # --- I term, with anti-windup clamping ---
        self._integral += error * dt
        self._integral = max(-self.integral_clamp, min(self.integral_clamp, self._integral))
        i_term = self.Ki * self._integral

        # --- D term ---
        derivative = (error - self._prev_error) / dt
        d_term = self.Kd * derivative
        self._prev_error = error

        steering = p_term + i_term + d_term
        steering = max(-self.max_angular_z, min(self.max_angular_z, steering))

        sharpness = min(1.0, abs(error))
        linear_speed = self.base_linear_speed - sharpness * (self.base_linear_speed - self.min_linear_speed)

        cmd = Twist()
        cmd.linear.x = float(linear_speed)
        cmd.angular.z = float(-steering)

        self.publisher.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = PIDControllerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
