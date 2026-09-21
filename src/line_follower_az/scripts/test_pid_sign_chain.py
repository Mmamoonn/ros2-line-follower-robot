#!/usr/bin/env python3
"""
Standalone sanity test for the PID -> Twist -> wheel-speed sign chain
used across pid_controller_node.py and motor_driver_node.py. Confirms
that when the line is detected to one side, the wheel speeds come out
asymmetric in the direction that actually steers the robot back toward
the line. No ROS2 needed.
"""

Kp, Ki, Kd = 0.8, 0.0, 0.0   # P-only for a clean directional check
wheel_radius = 0.033
wheel_separation = 0.15
base_speed = 0.12


def pid_to_twist(error):
    steering = Kp * error
    linear_x = base_speed
    angular_z = -steering   # same sign convention as pid_controller_node.py
    return linear_x, angular_z


def twist_to_wheels(linear_x, angular_z):
    v_left = (linear_x - angular_z * wheel_separation / 2.0) / wheel_radius
    v_right = (linear_x + angular_z * wheel_separation / 2.0) / wheel_radius
    return v_left, v_right


cases = [
    ("line to the LEFT (error<0) -> robot should turn LEFT", -0.5),
    ("line centered (error=0) -> straight", 0.0),
    ("line to the RIGHT (error>0) -> robot should turn RIGHT", 0.5),
]

print(f"{'case':55s} {'lin_x':>7s} {'ang_z':>7s} {'v_left':>7s} {'v_right':>7s}  verdict")
all_ok = True
for label, error in cases:
    lin_x, ang_z = pid_to_twist(error)
    v_left, v_right = twist_to_wheels(lin_x, ang_z)
    if error < 0:
        # turning left means the RIGHT wheel should spin faster than left
        ok = v_right > v_left
    elif error > 0:
        ok = v_left > v_right
    else:
        ok = abs(v_left - v_right) < 1e-6
    all_ok &= ok
    print(f"{label:55s} {lin_x:7.3f} {ang_z:7.3f} {v_left:7.3f} {v_right:7.3f}  "
          f"[{'OK' if ok else 'CHECK'}]")

print("\nRESULT:", "SIGN CONVENTION CONSISTENT END-TO-END" if all_ok else "MISMATCH FOUND")
