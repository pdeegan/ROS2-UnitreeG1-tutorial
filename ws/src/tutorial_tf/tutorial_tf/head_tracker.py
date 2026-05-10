"""Lesson 06 (dynamic): drive a head_yaw transform from a sine wave.

This is the dynamic counterpart to ``static_publisher``: a real
joint moves over time, so we use ``TransformBroadcaster`` (not the
``Static`` version) and emit a fresh transform per tick.

What goes wrong if you forget the timestamp
-------------------------------------------
TF buffers reject transforms whose stamps are older than the buffer
window. If you publish without updating ``header.stamp`` every
cycle, ``tf2_echo`` will work *once* and then go silent. The clock
moved on; your transform didn't.

Run it
------

::

    ros2 run tutorial_tf head_tracker
    # then:
    ros2 run tf2_ros tf2_echo head_link head_yaw_link
"""

from __future__ import annotations

import math

import rclpy
from geometry_msgs.msg import TransformStamped
from rclpy.node import Node
from tf2_ros import TransformBroadcaster


class HeadTracker(Node):
    def __init__(self) -> None:
        super().__init__("head_tracker")
        self.declare_parameter("rate_hz", 30.0)
        self.declare_parameter("amplitude_rad", 0.5)
        self.declare_parameter("period_s", 4.0)

        self._tf = TransformBroadcaster(self)
        rate = float(self.get_parameter("rate_hz").value)
        self._dt = 1.0 / rate
        self._t = 0.0
        self.create_timer(self._dt, self._tick)
        self.get_logger().info(f"broadcasting head_link → head_yaw_link @ {rate} Hz")

    def _tick(self) -> None:
        self._t += self._dt
        amp = float(self.get_parameter("amplitude_rad").value)
        period = float(self.get_parameter("period_s").value)
        yaw = amp * math.sin(2 * math.pi * self._t / period)

        tf = TransformStamped()
        tf.header.stamp = self.get_clock().now().to_msg()
        tf.header.frame_id = "head_link"
        tf.child_frame_id = "head_yaw_link"
        tf.transform.translation.x = 0.0
        tf.transform.translation.y = 0.0
        tf.transform.translation.z = 0.0
        tf.transform.rotation.z = math.sin(yaw / 2.0)
        tf.transform.rotation.w = math.cos(yaw / 2.0)
        self._tf.sendTransform(tf)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = HeadTracker()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
