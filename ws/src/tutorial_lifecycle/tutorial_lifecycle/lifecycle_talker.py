"""Lesson 05: a managed (lifecycle) node.

What this teaches
-----------------
A vanilla rclpy node is **always on** the moment ``rclpy.init()``
returns. For motion controllers and safety daemons, "always on" is
exactly wrong — you want a deliberate ``configure`` step that
allocates resources, an ``activate`` step that starts publishing
commands, and a ``deactivate`` step that stops without tearing
everything down.

Lifecycle nodes give you a state machine: ``unconfigured →
inactive → active → inactive → finalized``. Each transition is a
hook (``on_configure``, ``on_activate``, etc.) where you control
what happens. Subscribers and timers stay registered across
``active ↔ inactive``; the publisher stays alive but stops sending
in ``inactive``.

This is the right shape for the G1 bridge: configure when the SDK
is ready, activate only when the safety latch engages.

Run it
------

::

    ros2 run tutorial_lifecycle lifecycle_talker         # starts UNCONFIGURED
    # in a second shell:
    ros2 lifecycle list /lifecycle_talker                # available transitions
    ros2 lifecycle set  /lifecycle_talker configure
    ros2 lifecycle set  /lifecycle_talker activate
    ros2 topic echo /lifecycle_heartbeat                 # only now do messages flow
    ros2 lifecycle set  /lifecycle_talker deactivate     # publisher silent again
"""

from __future__ import annotations

import rclpy
from rclpy.lifecycle import LifecycleNode, LifecycleState, TransitionCallbackReturn
from std_msgs.msg import String


class LifecycleTalker(LifecycleNode):
    def __init__(self) -> None:
        super().__init__("lifecycle_talker")
        self._pub = None  # type: ignore[var-annotated]
        self._timer = None  # type: ignore[var-annotated]
        self._count = 0

    def on_configure(self, state: LifecycleState) -> TransitionCallbackReturn:
        self.get_logger().info("on_configure — allocating publisher")
        self._pub = self.create_lifecycle_publisher(String, "/lifecycle_heartbeat", 10)
        return TransitionCallbackReturn.SUCCESS

    def on_activate(self, state: LifecycleState) -> TransitionCallbackReturn:
        self.get_logger().info("on_activate — starting timer")
        self._timer = self.create_timer(1.0, self._tick)
        return super().on_activate(state)

    def on_deactivate(self, state: LifecycleState) -> TransitionCallbackReturn:
        self.get_logger().info("on_deactivate — stopping timer")
        if self._timer is not None:
            self._timer.cancel()
            self.destroy_timer(self._timer)
            self._timer = None
        return super().on_deactivate(state)

    def on_cleanup(self, state: LifecycleState) -> TransitionCallbackReturn:
        self.get_logger().info("on_cleanup — releasing publisher")
        if self._pub is not None:
            self.destroy_publisher(self._pub)
            self._pub = None
        return TransitionCallbackReturn.SUCCESS

    def on_shutdown(self, state: LifecycleState) -> TransitionCallbackReturn:
        self.get_logger().info("on_shutdown — finalizing")
        return TransitionCallbackReturn.SUCCESS

    def _tick(self) -> None:
        self._count += 1
        if self._pub is None:
            return
        msg = String()
        msg.data = f"heartbeat #{self._count}"
        self._pub.publish(msg)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = LifecycleTalker()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
