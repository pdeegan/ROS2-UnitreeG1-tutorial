"""Drive every joint of the Unitree G1 URDF for rviz visualization.

Publishes ``sensor_msgs/JointState`` at 30 Hz with one of these patterns:

* ``wave``    — right arm raised + waving, left arm at side.
* ``walk``    — alternating hip + knee swing, arms counter-swing.
* ``squat``   — slow knee/hip squat cycle, arms forward for balance.
* ``tpose``   — classic T-pose, arms straight out to the sides.
* ``stretch`` — slow rotation through shoulder + waist axes.
* ``zero``    — all joints at 0; URDF natural standing pose.

Change at runtime::

    ros2 param set /joint_animator pattern walk
    ros2 param set /joint_animator pattern stretch

This is the sole publisher of /joint_states for the G1 sim — every
one of the 29 revolute joints is driven (most relax to 0 in patterns
that don't move them, which is what robot_state_publisher needs to
render the full body without TF gaps).
"""

from __future__ import annotations

import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

# All 29 G1 revolute joints, canonical order.
G1_JOINTS = (
    # Legs (12)
    "left_hip_pitch_joint",   "left_hip_roll_joint",   "left_hip_yaw_joint",
    "left_knee_joint",
    "left_ankle_pitch_joint", "left_ankle_roll_joint",
    "right_hip_pitch_joint",  "right_hip_roll_joint",  "right_hip_yaw_joint",
    "right_knee_joint",
    "right_ankle_pitch_joint", "right_ankle_roll_joint",
    # Waist (3)
    "waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint",
    # Left arm (7)
    "left_shoulder_pitch_joint", "left_shoulder_roll_joint", "left_shoulder_yaw_joint",
    "left_elbow_joint",
    "left_wrist_roll_joint", "left_wrist_pitch_joint", "left_wrist_yaw_joint",
    # Right arm (7)
    "right_shoulder_pitch_joint", "right_shoulder_roll_joint", "right_shoulder_yaw_joint",
    "right_elbow_joint",
    "right_wrist_roll_joint", "right_wrist_pitch_joint", "right_wrist_yaw_joint",
)

assert len(G1_JOINTS) == 29


def _wave(t: float) -> dict[str, float]:
    """Right arm raised overhead, hand waving side-to-side."""
    sway = 0.4 * math.sin(2 * math.pi * t / 1.6)
    return {
        "right_shoulder_pitch_joint": -2.4,             # arm overhead
        "right_shoulder_roll_joint":  -0.5,
        "right_shoulder_yaw_joint":   -0.3,
        "right_elbow_joint":           1.2 + 0.4 * sway,
        "right_wrist_pitch_joint":     0.3 * sway,
        "left_shoulder_pitch_joint":   0.2,
        "left_shoulder_roll_joint":    0.2,
        "left_elbow_joint":            0.5,
    }


def _walk(t: float) -> dict[str, float]:
    """In-place gait: hips/knees alternate, arms counter-swing, slight torso roll."""
    phase = 2 * math.pi * t / 1.4
    s = math.sin(phase)
    c = math.cos(phase)
    return {
        "left_hip_pitch_joint":    +0.5 * s,
        "left_knee_joint":         +0.5 + 0.3 * (s + 1),
        "left_ankle_pitch_joint":  -0.2 * s,
        "right_hip_pitch_joint":   -0.5 * s,
        "right_knee_joint":        +0.5 + 0.3 * (1 - s),
        "right_ankle_pitch_joint": +0.2 * s,
        "left_shoulder_pitch_joint":  -0.4 * s,
        "left_elbow_joint":            0.6,
        "right_shoulder_pitch_joint": +0.4 * s,
        "right_elbow_joint":           0.6,
        "waist_roll_joint":            0.05 * c,
    }


def _squat(t: float) -> dict[str, float]:
    """Slow squat — knees + hips bend together, arms forward for balance."""
    depth = (1 - math.cos(2 * math.pi * t / 4.0)) / 2.0  # 0..1, 4s period
    return {
        "left_hip_pitch_joint":    -1.0 * depth,
        "right_hip_pitch_joint":   -1.0 * depth,
        "left_knee_joint":         +1.8 * depth,
        "right_knee_joint":        +1.8 * depth,
        "left_ankle_pitch_joint":  -0.8 * depth,
        "right_ankle_pitch_joint": -0.8 * depth,
        "left_shoulder_pitch_joint":  -1.0 * depth,
        "right_shoulder_pitch_joint": -1.0 * depth,
        "left_elbow_joint":            0.3,
        "right_elbow_joint":           0.3,
    }


def _tpose(_t: float) -> dict[str, float]:
    """Classic T-pose — arms straight out."""
    return {
        "left_shoulder_roll_joint":   1.5,
        "right_shoulder_roll_joint": -1.5,
    }


def _stretch(t: float) -> dict[str, float]:
    """Slow circular rotation through shoulder + waist axes."""
    p = 2 * math.pi * t / 6.0
    return {
        "waist_yaw_joint":             0.4 * math.sin(p),
        "waist_pitch_joint":           0.2 * math.sin(p + math.pi / 2),
        "left_shoulder_pitch_joint":  -1.0 * math.sin(p),
        "left_shoulder_roll_joint":   +0.6 * math.cos(p),
        "right_shoulder_pitch_joint": -1.0 * math.sin(p + math.pi),
        "right_shoulder_roll_joint":  -0.6 * math.cos(p),
        "left_elbow_joint":            1.0 + 0.5 * math.sin(p * 1.3),
        "right_elbow_joint":           1.0 + 0.5 * math.cos(p * 1.3),
    }


_PATTERNS = {
    "wave":    _wave,
    "walk":    _walk,
    "squat":   _squat,
    "tpose":   _tpose,
    "stretch": _stretch,
    "zero":    lambda _t: {},
}


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
            f"rate={rate}Hz, driving {len(G1_JOINTS)} joints"
        )
        self.get_logger().info(
            "patterns: " + ", ".join(_PATTERNS.keys())
        )
        self.get_logger().info(
            "change at runtime: ros2 param set /joint_animator pattern <name>"
        )

    def _tick(self) -> None:
        self._t += self._dt
        pattern = str(self.get_parameter("pattern").value)
        fn = _PATTERNS.get(pattern, _PATTERNS["zero"])
        overrides = fn(self._t)

        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = list(G1_JOINTS)
        msg.position = [overrides.get(name, 0.0) for name in G1_JOINTS]
        self._pub.publish(msg)


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
