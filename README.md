# ROS 2 Line Follower Robot

A robust, modular line-following robot built with **ROS 2** and **Python**, featuring a closed-loop **PID control system** for processing track data and dynamically adjusting differential-drive velocities in a simulated Gazebo environment.

The architecture is designed with **hardware-in-the-loop transitions** in mind. The software stack mirrors the structure required for a physical Arduino-based robot, allowing deployment to real hardware by replacing the simulation sensor and actuator interfaces.

---

## 🚀 Key Features & Performance Optimizations

* **Low-Latency Control Loop**
  Uses `qos_profile_sensor_data` with **Best Effort** QoS across the sensor pipeline. Stale camera frames and sensor readings are dropped rather than queued, reducing control lag and improving responsiveness around sharp corners.

* **Dynamic PID Parameter Tuning**
  Implements a ROS 2 parameter callback so that `Kp`, `Ki`, `Kd`, and speed constraints can be modified at runtime without restarting the simulation or recompiling the package.

* **Intelligent Cornering**
  Dynamically reduces the base linear velocity as the line-tracking error increases, allowing the robot to slow down before sharper turns.

* **Modular Control Architecture**
  Separates sensing, control, and motor-command processing into independent ROS 2 nodes, making the system easier to debug, extend, and transfer to physical hardware.

* **Differential-Drive Kinematics**
  Converts commanded `Twist` velocities into corresponding left- and right-wheel velocity commands.

* **Build & Simulation Automation**
  Includes a custom `Makefile` for workspace building, cleaning, simulation startup, monitoring, and automated Tilix multi-pane terminal management.

* **Procedural Track Generation**
  Includes `generate_track.py` for creating new and increasingly complex test tracks to evaluate controller performance.

---

## 🏗️ System Architecture

The system is divided into three primary processing stages:

```text
                 Camera Image
                      │
                      ▼
              ┌────────────────┐
              │  sensor_node   │
              │                │
              │ ROI Processing │
              │ 5 Virtual IR   │
              │ Zones          │
              └───────┬────────┘
                      │
                /line_sensor
                      │
                      ▼
             ┌──────────────────┐
             │ pid_controller   │
             │                  │
             │ PID Control      │
             │ Speed Scaling    │
             └────────┬─────────┘
                      │
                   /cmd_vel
                      │
              ┌───────┴─────────┐
              │                 │
              ▼                 ▼
       Gazebo DiffDrive    motor_driver
          Plugin               │
                              ▼
                     /wheel_velocity
```

### ROS 2 Nodes

| Node             | Input Topic                               | Output Topic                                     | Role                                                                                                                                                                                    |
| ---------------- | ----------------------------------------- | ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sensor_node`    | `/camera/image_raw` (`sensor_msgs/Image`) | `/line_sensor` (`std_msgs/Float32`)              | Processes the downward-facing camera image, extracts the line from the ROI, divides it into five virtual sensor zones, and calculates a normalized tracking error from `-1.0` to `1.0`. |
| `pid_controller` | `/line_sensor` (`std_msgs/Float32`)       | `/cmd_vel` (`geometry_msgs/Twist`)               | Calculates proportional, integral, and derivative steering corrections and combines them with dynamic linear-speed control.                                                             |
| `motor_driver`   | `/cmd_vel` (`geometry_msgs/Twist`)        | `/wheel_velocity` (`std_msgs/Float32MultiArray`) | Converts differential-drive `Twist` commands into left- and right-wheel velocity commands.                                                                                              |

> **Simulation Note:**
> In Gazebo, the DiffDrive plugin directly consumes `/cmd_vel`. The `motor_driver` node remains active to provide wheel-command telemetry and maintain architectural parity with a future physical robot implementation.

---

## ⚙️ Requirements

See [`REQUIREMENTS.md`](REQUIREMENTS.md) for the complete dependency list, supported versions, ROS 2 packages, and system requirements.

### Core Environment

* **OS:** Ubuntu 24.04 LTS
* **ROS 2:** Jazzy Jalisco
* **Simulation:** Gazebo Harmonic (Default for ROS 2 Jazzy)
* **Programming Language:** Python 3
* **Terminal Automation:** Tilix

### Install System Dependencies

```bash
sudo apt update

sudo apt install \
    ros-jazzy-ros-gz \
    tilix \
    rqt \
    ros-jazzy-rqt-reconfigure
```
---

## 🛠️ Installation & Build

### 1. Create a ROS 2 Workspace

```bash
mkdir -p ~/ros2_az/src
cd ~/ros2_az/src
```

### 2. Clone the Repository

```bash
git clone <repository_url> line_follower_az
```

### 3. Install ROS Dependencies

```bash
cd ~/ros2_az

rosdep update
rosdep install --from-paths src -y --ignore-src
```

### 4. Build the Workspace

The project includes a custom `Makefile` that simplifies the build process.

```bash
make build
```

---

## 🕹️ Usage

For complete usage instructions, including simulation startup, PID tuning, monitoring, and workspace maintenance, see [`Usage.md`](Usage.md).

### Quick Start

Launch the complete simulation environment using:

```bash
make sim
```

The automated Tilix layout provides:

* **Left Pane:** Gazebo interface and ROS-Gazebo bridge
* **Top-Right Pane:** Sensor, PID, and motor-driver logs
* **Bottom-Right Pane:** Live `/cmd_vel` telemetry

---

## 🎛️ PID Control

The line-following controller uses a conventional PID formulation:

```text
Control Output = Kp × Error
              + Ki × Integral(Error)
              + Kd × Derivative(Error)
```

The normalized line error is calculated within:

```text
-1.0 ─────────── 0.0 ─────────── +1.0
 Left            Center           Right
```

The controller uses this error to adjust the robot's angular velocity while dynamically scaling its linear velocity.

### PID Parameters

| Parameter           | Purpose                                                                    |
| ------------------- | -------------------------------------------------------------------------- |
| `Kp`                | Controls the strength of the immediate steering correction.                |
| `Ki`                | Corrects accumulated tracking error and long-term drift.                   |
| `Kd`                | Dampens rapid error changes and improves stability around sharp turns.     |
| `base_linear_speed` | Defines the robot's maximum forward speed on relatively straight sections. |

For typical line-following applications, `Ki` can be kept low or disabled because accumulated error is often less useful than proportional and derivative correction.

---

## 📂 Project Structure

```text
ros2_lf/
├── Makefile                         # Build, simulation & automation commands
├── README.md                        # Project overview and documentation
├── REQUIREMENTS.md                  # System and software requirements
├── Usage.md                         # Detailed usage instructions
│
└── src/
    └── line_follower_az/
        ├── config/                  # YAML configuration and parameters
        ├── description/             # URDF/XACRO robot descriptions
        ├── launch/                  # ROS 2 launch files
        │   ├── nodes.launch.py
        │   └── simulation.launch.py
        │
        ├── line_follower_az/        # Main Python ROS 2 package
        │   ├── sensor_node.py
        │   ├── pid_controller.py
        │   └── motor_driver.py
        │
        ├── scripts/                 # Utility and testing scripts
        │   ├── generate_track.py
        │   └── ...
        │
        └── worlds/                  # Gazebo simulation environments
            └── ...
```

---

## 🔄 Hardware Transition

The project follows a modular architecture intended to simplify migration from simulation to a physical robot.

The primary components that would need to be replaced or adapted are:

```text
Simulation                     Physical Robot
──────────                     ──────────────

Camera Image      ───────►     IR Sensor Array
     │                              │
     ▼                              ▼
sensor_node        ───────►     sensor_node
     │                              │
     └──────────────┬───────────────┘
                    ▼
             PID Controller
                    │
                    ▼
                /cmd_vel
                    │
                    ▼
             Motor Interface
                    │
                    ▼
              Physical Motors
```

The **PID controller and high-level control architecture can remain largely unchanged**, while the sensor acquisition and motor-output layers can be adapted for the target hardware.

---

## 🧪 Testing & Evaluation

The included procedural track generator can be used to create different track configurations and evaluate controller behavior under varying conditions.

Example:

```bash
python3 scripts/generate_track.py
```

Potential evaluation metrics include:

* Line-tracking stability
* Lap completion time
* Maximum sustainable speed
* Cornering behavior
* Tracking error
* Overshoot
* Recovery time after losing the line
* Controller response to sharp turns

---

## 🧹 Workspace Maintenance

To remove previous build artifacts:

```bash
make clean
```

Then rebuild the workspace:

```bash
make build
```

This can be useful after:

* Renaming ROS 2 nodes
* Modifying package dependencies
* Changing package structure
* Updating launch files
* Experiencing stale build/install artifacts

---

## 📖 Documentation

| Document                             | Description                                                                      |
| ------------------------------------ | -------------------------------------------------------------------------------- |
| [`README.md`](README.md)             | Project overview, architecture, installation, and technical details              |
| [`REQUIREMENTS.md`](REQUIREMENTS.md) | Complete system, software, ROS 2, and dependency requirements                    |
| [`Usage.md`](Usage.md)               | Detailed instructions for launching, monitoring, tuning, and operating the robot |

---

