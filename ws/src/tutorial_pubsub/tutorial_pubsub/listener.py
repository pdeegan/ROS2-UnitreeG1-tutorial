"""Lesson 02 (listener): subscribe to /joint_state, print a summary.

The subscriber QoS must be **compatible** with the publisher's. If
the talker uses ``sensor_data`` and the listener defaults to
``reliable``, the listener will silently never receive a message —
DDS treats QoS mismatch as "they're not for each other."

Run it (after the talker is publishing)
---------------------------------------
``ros2 run tutorial_pubsub listener``

You should see a row every callback. If you see nothing, run::

    ros2 topic info /joint_state -v

and look at the Subscription QoS — if it says "incompatible", that's
your bug.
"""

from __future__ import annotations

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import JointState


class JointListener(Node):
    def __init__(self) -> None:
        super().__init__("joint_listener")
        self._sub = self.create_subscription(
            JointState, "/joint_state", self._on_state, qos_profile_sensor_data
        )
        self._count = 0
        self.get_logger().info("subscribed to /joint_state with sensor_data QoS")

    def _on_state(self, msg: JointState) -> None:
        self._count += 1
        if self._count % 25 == 1:
            positions = ", ".join(f"{p:+.3f}" for p in msg.position)
            self.get_logger().info(
                f"rx#{self._count:>5d}  pos=[{positions}]"
            )


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = JointListener()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
