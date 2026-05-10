"""Animate joint positions on a fake humanoid for rviz visualization.

Publishes ``sensor_msgs/JointState`` at 30 Hz with one of three patterns:

* ``wave`` — arms waving overhead (the default)
* ``walk`` — alternating hip pitch + arm swing
* ``zero`` — all joints at zero, useful for verifying the URDF zero pose

Change the pattern at runtime with the ``pattern`` parameter::

    ros2 param set /joint_animator pattern walk
    ros2 param set /joint_animator pattern wave

This node is what makes the URDF in rviz come alive without a real robot.
"""

from __future__ import annotations

import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

# Joints we animate. We publish each name in BOTH the short form (toy URDF
# uses these) AND the `_joint`-suffixed form (the real Unitree G1 URDF uses
# these). robot_state_publisher silently ignores names that aren't in its
# URDF, so this list works for both.
_BASE_NAMES = (
    "left_shoulder_pitch",
    "right_shoulder_pitch",
    "left_elbow",
    "right_elbow",
    "left_hip_pitch",
    "right_hip_pitch",
)
JOINTS = _BASE_NAMES + tuple(n + "_joint" for n in _BASE_NAMES)


class Animator(Node):
    def __init__(self) -> None:
        super().__init__("joint_animator")
        self.declare_parameter("pattern", "wave")
        self.declare_parameter("rate_hz", 30.0)

        rate = float(self.get_parameter("rate_hz").value)
        self._pub = self.create_publisher(JointState, "/joint_states", 10)
        self._dt = 1.0 / rate
        self._t = 0.0
        self._timer = self.create_timer(self._dt, self._tick)
        self.get_logger().info(
            f"animator up — pattern={self.get_parameter('pattern').value} rate={rate}Hz"
        )
        self.get_logger().info(
            "change pattern at runtime: ros2 param set /joint_animator pattern {wave|walk|zero}"
        )

    def _tick(self) -> None:
        self._t += self._dt
        pattern = str(self.get_parameter("pattern").value)
        base = self._compute_positions(pattern, self._t)  # 6 values
        # Duplicate to cover both naming conventions (toy URDF + real G1).
        positions = base + base
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = list(JOINTS)
        msg.position = positions
        self._pub.publish(msg)

    @staticmethod
    def _compute_positions(pattern: str, t: float) -> list[float]:
        if pattern == "zero":
            return [0.0] * len(_BASE_NAMES)
        if pattern == "walk":
            phase = 2 * math.pi * t / 1.6  # 0.625 Hz gait
            return [
                +0.3 * math.sin(phase),                    # L sh pitch (arm fwd)
                -0.3 * math.sin(phase),                    # R sh pitch (arm bwd)
                +0.4 + 0.1 * math.cos(phase),              # L elbow (mild swing)
                +0.4 - 0.1 * math.cos(phase),              # R elbow
                -0.4 * math.sin(phase),                    # L hip (leg back)
                +0.4 * math.sin(phase),                    # R hip (leg fwd)
            ]
        # default: wave
        phase = 2 * math.pi * t / 3.0
        return [
            -1.5 + 0.3 * math.sin(phase),  # L shoulder up
            -1.5 + 0.3 * math.sin(phase + math.pi),  # R shoulder up (opposite)
            +0.5 + 0.4 * math.sin(phase),
            +0.5 + 0.4 * math.sin(phase + math.pi),
            0.0,
            0.0,
        ]


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = Animator()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
