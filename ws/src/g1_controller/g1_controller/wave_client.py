"""Lesson 09 (client): trigger a wave via /g1/set_mode.

This is the smallest possible 'use the controller' script — a
one-shot client that engages safety, calls set_mode(WAVE_HAND), and
releases safety on the way out.

Run after bringing up bridge + safety + controller and configuring
the controller's lifecycle.
"""

from __future__ import annotations

import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger


class WaveClient(Node):
    def __init__(self) -> None:
        super().__init__("wave_client")
        self._engage = self.create_client(Trigger, "/g1/safety/engage")
        self._release = self.create_client(Trigger, "/g1/safety/release")
        try:
            from humanoid_msgs.srv import SetMode
            self._set_mode = self.create_client(SetMode, "/g1/set_mode")
            self._SetMode = SetMode
        except ImportError:
            self.get_logger().error("humanoid_msgs not built — build it first")
            raise

    def run(self) -> int:
        if not all(c.wait_for_service(2.0) for c in (self._engage, self._release, self._set_mode)):
            self.get_logger().error("one or more services unavailable")
            return 1

        from humanoid_msgs.msg import SportMode

        self.get_logger().info("engaging safety …")
        self._call(self._engage, Trigger.Request())

        try:
            self.get_logger().info("requesting WAVE_HAND …")
            req = self._SetMode.Request()
            req.mode = SportMode()
            req.mode.mode = SportMode.WAVE_HAND
            future = self._set_mode.call_async(req)
            rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
            resp = future.result()
            if resp is None or not resp.success:
                self.get_logger().error(
                    f"set_mode failed: {getattr(resp, 'message', 'no response')}"
                )
                return 1
            self.get_logger().info(f"set_mode OK: {resp.message}")
            return 0
        finally:
            self.get_logger().info("releasing safety …")
            self._call(self._release, Trigger.Request())

    def _call(self, client, req):  # type: ignore[no-untyped-def]
        future = client.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=2.0)
        return future.result()


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = WaveClient()
    rc = node.run()
    node.destroy_node()
    rclpy.try_shutdown()
    raise SystemExit(rc)


if __name__ == "__main__":
    main()
