"""Listen to /cmd_vel (geometry_msgs/Twist) and log the commanded velocity.

This is the consumer end of a ``teleop_twist_keyboard`` session — drives
home the point that any tool that publishes to ``/cmd_vel`` can drive any
robot that subscribes to it. The topic is the contract; the implementation
on either side is interchangeable.

Run it::

    ros2 run tutorial_sim twist_listener
    # then in another shell:
    ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/cmd_vel
"""

from __future__ import annotations

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node


class TwistListener(Node):
    def __init__(self) -> None:
        super().__init__("twist_listener")
        self._sub = self.create_subscription(Twist, "/cmd_vel", self._on_twist, 10)
        self._last_nonzero = None
        self.get_logger().info("listening to /cmd_vel — try teleop_twist_keyboard to drive")

    def _on_twist(self, msg: Twist) -> None:
        vx, wz = msg.linear.x, msg.angular.z
        bar_len = int(min(abs(vx) * 20, 20))
        bar = ("→" if vx >= 0 else "←") * bar_len
        spin = ("⟳" if wz >= 0 else "⟲") * int(min(abs(wz) * 5, 5))
        self.get_logger().info(f"vx={vx:+.2f} m/s {bar:<22}  wz={wz:+.2f} rad/s {spin}")


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = TwistListener()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
