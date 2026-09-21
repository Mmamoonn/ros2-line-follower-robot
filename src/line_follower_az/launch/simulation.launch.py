#!/usr/bin/env python3
"""
launch/simulation.launch.py  (v3 -- robot embedded in world, no spawn step)

The robot model is now part of worlds/line_track.world (SDF native),
so it appears the instant Gazebo loads the world -- zero timing dependency,
zero spawn-service race conditions.

This file still starts robot_state_publisher so ROS2 has the TF tree
(needed for rviz2 and the ROS2 side of things), but Gazebo's physics and
rendering come entirely from the SDF embedded in the world file.

Startup sequence:
  t=0s   Gazebo Sim loads world (robot is already inside it)
  t=3s   ros_gz_bridge connects ROS2 topics to Gazebo topics
  t=8s   The 5 project nodes start (sensor, pid, motor, logger, monitor)
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    pkg_share       = get_package_share_directory('line_follower_az')
    ros_gz_sim_share = get_package_share_directory('ros_gz_sim')

    world_path      = os.path.join(pkg_share, 'worlds', 'line_track.world')
    urdf_path       = os.path.join(pkg_share, 'description', 'line_follower.urdf')
    bridge_cfg_path = os.path.join(pkg_share, 'config',      'bridge_config.yaml')
    params_path     = os.path.join(pkg_share, 'config',      'pid_params.yaml')

    with open(urdf_path, 'r') as f:
        robot_description_content = f.read()

    # ------------------------------------------------------------------
    # 1. Gazebo Sim -- robot model is INSIDE the world file (no spawn)
    # ------------------------------------------------------------------
    gz_sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_share, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r {world_path}'}.items(),
    )

    # ------------------------------------------------------------------
    # 2. robot_state_publisher -- publishes TF tree for ROS2/rviz2.
    #    use_sim_time=False so it starts immediately (no clock dependency).
    # ------------------------------------------------------------------
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'robot_description': robot_description_content,
            'use_sim_time': False,
        }],
    )

    # ------------------------------------------------------------------
    # 3. ROS2 <-> Gazebo bridge (at 3 s -- world loads in < 3 s normally)
    # ------------------------------------------------------------------
    bridge_node = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ros_gz_bridge',
        output='screen',
        parameters=[{'config_file': bridge_cfg_path,
                     'use_sim_time': False}],
    )

    # ------------------------------------------------------------------
    # 4. The 5 project nodes (at 8 s -- bridge must be live first)
    # ------------------------------------------------------------------
    def make_node(executable):
        return Node(
            package='line_follower_az',
            executable=executable,
            name=executable,
            output='screen',
            parameters=[params_path, {'use_sim_time': False}],
        )

    pipeline_nodes = [
        make_node('sensor_node'),
        make_node('pid_controller_node'),
        make_node('motor_driver_node'),
        make_node('logger_node'),
        make_node('monitor_node'),
    ]

    return LaunchDescription([
        gz_sim_launch,
        robot_state_publisher_node,
        TimerAction(period=3.0, actions=[bridge_node]),
        TimerAction(period=8.0, actions=pipeline_nodes),
    ])
