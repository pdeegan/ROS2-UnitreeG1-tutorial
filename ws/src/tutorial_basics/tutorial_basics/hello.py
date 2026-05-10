"""Lesson 01: a minimal ROS 2 node.

What this teaches
-----------------
ROS 2 isn't a framework you import into ``main()``; it's a runtime
you join. ``rclpy.init()`` registers this process with the ROS 2
middleware (the RMW — Cyclone DDS in this tutorial). ``rclpy.spin()``
hands the executor your callbacks. ``rclpy.try_shutdown()`` un-registers.

A node that forgets ``destroy_node()`` leaks a DDS participant; the
robot will discover it again on the next launch and your topic
graph fills with ghosts. ``try/finally`` around ``spin`` is not
boilerplate — it's the contract.

Run it
------
``ros2 run tutorial_basics hello``

What you'll see: a heartbeat log every second with the wall-clock
time and a counter. Ctrl+C to stop; observe the clean shutdown line.
"""

from __future__ import annotations

import rclpy
from rclpy.node import Node


class Hello(Node):
    def __init__(self) -> None:
        super().__init__("hello")
        self.declare_parameter("period_s", 1.0)
        self.declare_parameter("greeting", "hello, humanoid")
        period = float(self.get_parameter("period_s").value)
        self._count = 0
        self._timer = self.create_timer(period, self._tick)
        self.get_logger().info(
            f"node up — name={self.get_name()} period={period}s"
        )

    def _tick(self) -> None:
        self._count += 1
        greeting = str(self.get_parameter("greeting").value)
        self.get_logger().info(f"{greeting} (tick {self._count})")


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = Hello()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        node.get_logger().info("interrupted — shutting down cleanly")
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
