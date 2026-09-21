#!/usr/bin/env python3
"""
monitor_node.py

Role in the architecture:
    Subscribes: /wheel_velocity
    Publishes : nothing (matches the Node Architecture table)

What it does:
    A tiny, dependency-free "dashboard" you can watch in a terminal while
    the robot runs, without needing to open rqt_plot. Once a second it
    prints the current left/right wheel speeds, their average (rough
    forward speed indicator) and their difference (how hard the robot is
    currently steering). Handy for a quick sanity check during Task 4/5
    integration testing, before you bother with the heavier visualisation
    tools from Section 7.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32MultiArray


class MonitorNode(Node):
    def __init__(self):
        super().__init__('monitor_node')

        self.declare_parameter('print_rate_hz', 1.0)

        self._latest = [0.0, 0.0]
        self.create_subscription(
            Float32MultiArray, '/wheel_velocity', self._wheel_cb, 10)

        print_rate_hz = self.get_parameter('print_rate_hz').value
        period = 1.0 / print_rate_hz if print_rate_hz > 0 else 1.0
        self._timer = self.create_timer(period, self._print_status)

        self.get_logger().info("monitor_node ready. Printing wheel speeds.")

    def _wheel_cb(self, msg: Float32MultiArray):
        if len(msg.data) >= 2:
            self._latest = [msg.data[0], msg.data[1]]

    def _print_status(self):
        left, right = self._latest
        avg = (left + right) / 2.0
        diff = right - left
        self.get_logger().info(
            f"L={left:+6.2f} rad/s  R={right:+6.2f} rad/s  "
            f"avg={avg:+6.2f}  steer_diff={diff:+6.2f}")


def main(args=None):
    rclpy.init(args=args)
    node = MonitorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
