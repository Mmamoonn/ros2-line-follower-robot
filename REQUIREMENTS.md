# Project Requirements

## System Specifications
* **Operating System:** Ubuntu 24.04 LTS
* **Middleware:** ROS 2 Jazzy Jalisco
* **Terminal Emulator:** Tilix (Required for Make automation)
* **Simulation Environment:** Gazebo Harmonic (Default for ROS 2 Jazzy)

## Python Dependencies
The Python nodes utilize standard ROS 2 libraries. Ensure you have the following packages installed:
* `rclpy`
* `geometry_msgs`
* `sensor_msgs`
* `std_msgs`
* `setuptools`

## Installation
To install the system-level dependencies required for this project:

```bash
sudo apt update
sudo apt install ros-jazzy-ros-gz tilix rqt ros-jazzy-rqt-reconfigure
rosdep update
rosdep install --from-paths src -y --ignore-src
