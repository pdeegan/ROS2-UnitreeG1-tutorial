"""Lesson 02 (talker): publish a simulated joint state.

What this teaches
-----------------
QoS is not a stylistic choice. A humanoid IMU publisher at 500 Hz
with the default ``reliable`` profile will retransmit dropped
samples and saturate the network; an emergency stop topic with
``best_effort`` will silently lose the message that mattered.

This publisher uses ``sensor_data`` QoS — ``best_effort, volatile,
keep_last(5)`` — because joint state is a fresh sample every cycle.
A dropped one isn't worth retransmitting; the next one is already
on the way.

Run it
------
``ros2 run tutorial_pubsub talker``

Then in a second shell::

    ros2 topic echo /joint_state
    ros2 topic hz /joint_state          # confirm 50 Hz
    ros2 topic info /joint_state -v     # see the QoS profile in use

Note: this lesson uses the singular ``/joint_state`` (not the
conventional plural ``/joint_states``) deliberately, so it can run
alongside ``tutorial_sim`` without two publishers fighting over the
same topic. Real production code should use ``/joint_states``.
"""

from __future__ import annotations

import math

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import JointState

JOINT_NAMES = ("left_shoulder", "right_shoulder", "left_elbow", "right_elbow")


class FakeJointTalker(Node):
    def __init__(self) -> None:
        super().__init__("fake_joint_talker")
        self.declare_parameter("rate_hz", 50.0)
        self.declare_parameter("amplitude_rad", 0.5)

        self._pub = self.create_publisher(
            JointState, "/joint_state", qos_profile_sensor_data
        )

        rate = float(self.get_parameter("rate_hz").value)
        self._amp = float(self.get_parameter("amplitude_rad").value)
        self._timer = self.create_timer(1.0 / rate, self._tick)
        self._t = 0.0
        self._dt = 1.0 / rate
        self.get_logger().info(
            f"publishing /joint_state @ {rate} Hz, QoS=sensor_data"
        )

    def _tick(self) -> None:
        self._t += self._dt
        msg = JointState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.name = list(JOINT_NAMES)
        msg.position = [
            self._amp * math.sin(self._t),
            self._amp * math.sin(self._t + math.pi),
            self._amp * 0.5 * math.cos(self._t),
            self._amp * 0.5 * math.cos(self._t + math.pi),
        ]
        self._pub.publish(msg)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = FakeJointTalker()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
