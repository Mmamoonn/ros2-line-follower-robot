#!/usr/bin/env python3
"""
launch/nodes.launch.py

Launches the 5 ROS2 nodes that make up the software side of the project:
sensor_node, pid_controller_node, motor_driver_node, logger_node and
monitor_node. All of them load their tunable values from
config/pid_params.yaml.

Run on its own (useful once Gazebo + the robot are already up, e.g. you
restarted just the control nodes after editing PID gains):
    ros2 launch line_follower_az nodes.launch.py

Normally you won't call this directly -- simulation.launch.py includes it
automatically after bringing up Gazebo and the robot.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share = get_package_share_directory('line_follower_az')
    params_file = os.path.join(pkg_share, 'config', 'pid_params.yaml')

    return LaunchDescription([
        Node(
            package='line_follower_az',
            executable='sensor_node',
            name='sensor_node',
            output='screen',
            parameters=[params_file],
        ),
        Node(
            package='line_follower_az',
            executable='pid_controller_node',
            name='pid_controller_node',
            output='screen',
            parameters=[params_file],
        ),
        Node(
            package='line_follower_az',
            executable='motor_driver_node',
            name='motor_driver_node',
            output='screen',
            parameters=[params_file],
        ),
        Node(
            package='line_follower_az',
            executable='logger_node',
            name='logger_node',
            output='screen',
            parameters=[params_file],
        ),
        Node(
            package='line_follower_az',
            executable='monitor_node',
            name='monitor_node',
            output='screen',
            parameters=[params_file],
        ),
    ])
