"""Animate joint positions on a fake humanoid for rviz visualization.

Publishes ``sensor_msgs/JointState`` at 30 Hz with one of three patterns:

* ``wave`` — arms waving overhead (the default)
* ``walk`` — alternating hip pitch + arm swing
* ``zero`` — all joints at zero, useful for verifying the URDF zero pose

Change the pattern at runtime with the ``pattern`` parameter::

    ros2 param set /joint_animator pattern walk
    ros2 param set /joint_animator pattern wave

This node is what makes the URDF in rviz come alive without a real robot.
We publish positions for **every** joint robot_state_publisher might
expect — the toy URDF's 6 short names AND the real Unitree G1's
29 ``_joint``-suffixed names — at 0.0 except for the six we animate.
robot_state_publisher silently ignores names that aren't in its URDF,
so the same message drives both robots.
"""

from __future__ import annotations

import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

# Six joints we actively animate.
_ANIMATED = (
    "left_shoulder_pitch",
    "right_shoulder_pitch",
    "left_elbow",
    "right_elbow",
    "left_hip_pitch",
    "right_hip_pitch",
)

# All 29 G1 (revolute) joint names — we keep these at 0.0 except for the
# six animated ones above. Without publishing the full set, the real G1
# URDF's TF tree has gaps that look like the body has collapsed.
_G1_ALL = (
    "left_hip_pitch_joint",
    "left_hip_roll_joint",
    "left_hip_yaw_joint",
    "left_knee_joint",
    "left_ankle_pitch_joint",
    "left_ankle_roll_joint",
    "right_hip_pitch_joint",
    "right_hip_roll_joint",
    "right_hip_yaw_joint",
    "right_knee_joint",
    "right_ankle_pitch_joint",
    "right_ankle_roll_joint",
    "waist_yaw_joint",
    "waist_roll_joint",
    "waist_pitch_joint",
    "left_shoulder_pitch_joint",
    "left_shoulder_roll_joint",
    "left_shoulder_yaw_joint",
    "left_elbow_joint",
    "left_wrist_roll_joint",
    "left_wrist_pitch_joint",
    "left_wrist_yaw_joint",
    "right_shoulder_pitch_joint",
    "right_shoulder_roll_joint",
    "right_shoulder_yaw_joint",
    "right_elbow_joint",
    "right_wrist_roll_joint",
    "right_wrist_pitch_joint",
    "right_wrist_yaw_joint",
)

# Names → index into the 6-value `base` array. Anything not in this
# mapping defaults to 0.0.
_INDEX = {
    "left_shoulder_pitch": 0,
    "right_shoulder_pitch": 1,
    "left_elbow": 2,
    "right_elbow": 3,
    "left_hip_pitch": 4,
    "right_hip_pitch": 5,
    "left_shoulder_pitch_joint": 0,
    "right_shoulder_pitch_joint": 1,
    "left_elbow_joint": 2,
    "right_elbow_joint": 3,
    "left_hip_pitch_joint": 4,
    "right_hip_pitch_joint": 5,
}

# Final flat name list: toy URDF's short names + every G1 joint.
JOINTS = _ANIMATED + _G1_ALL


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
            f"animator up — pattern={self.get_parameter('pattern').value} "
            f"rate={rate}Hz publishing {len(JOINTS)} joint names"
        )
        self.get_logger().info(
            "change pattern at runtime: ros2 param set /joint_animator pattern {wave|walk|zero}"
        )

    def _tick(self) -> None:
        self._t += self._dt
        pattern = str(self.get_parameter("pattern").value)
        base = self._compute_positions(pattern, self._t)  # 6 values
        positions = [base[_INDEX[n]] if n in _INDEX else 0.0 for n in JOINTS]
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = list(JOINTS)
        msg.position = positions
        self._pub.publish(msg)

    @staticmethod
    def _compute_positions(pattern: str, t: float) -> list[float]:
        if pattern == "zero":
            return [0.0] * 6
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
            -1.5 + 0.3 * math.sin(phase),                  # L shoulder up
            -1.5 + 0.3 * math.sin(phase + math.pi),        # R shoulder up
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
