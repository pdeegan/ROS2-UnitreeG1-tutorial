"""Lesson 06 (static): publish the body→head static transform.

What this teaches
-----------------
TF2 is the answer to "where is X relative to Y?" for an entire robot
graph, queryable at any time, at any historical timestamp. Without
it, every node that needs the head pose ends up subscribing to the
joint state and doing its own kinematics — wrong, slow, drifts.

Static transforms (`StaticTransformBroadcaster`) are for frames that
don't move during a run: sensor mountings, link offsets, robot →
world initial pose. They're published once, latched, and queryable
forever — cheaper than streaming them every cycle.

The G1's head is ~270 mm above the chest joint, offset 0 in x, 0 in
y in its zero-pose. That's the transform we publish here.

Run it
------

::

    ros2 run tutorial_tf static_publisher
    # then in another shell:
    ros2 run tf2_ros tf2_echo base_link head_link
"""

from __future__ import annotations

import rclpy
from geometry_msgs.msg import TransformStamped
from rclpy.node import Node
from tf2_ros.static_transform_broadcaster import StaticTransformBroadcaster


class StaticPublisher(Node):
    def __init__(self) -> None:
        super().__init__("static_publisher")
        self._tf = StaticTransformBroadcaster(self)

        tf = TransformStamped()
        tf.header.stamp = self.get_clock().now().to_msg()
        tf.header.frame_id = "base_link"
        tf.child_frame_id = "head_link"
        tf.transform.translation.x = 0.0
        tf.transform.translation.y = 0.0
        tf.transform.translation.z = 0.27  # G1 chest → head ≈ 270 mm
        tf.transform.rotation.w = 1.0      # identity rotation

        self._tf.sendTransform(tf)
        self.get_logger().info(
            "published static transform base_link → head_link (z=0.27 m)"
        )


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = StaticPublisher()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
