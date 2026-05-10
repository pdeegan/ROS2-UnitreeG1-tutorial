"""Lesson 03 (client): call the posture services.

Why is this its own node instead of a one-shot ``ros2 service call``?
Because a real client cares about:

* whether the server is reachable at all (``wait_for_service``);
* whether the call returns within a timeout;
* what to do on failure (retry? back off? page someone?).

The CLI ``ros2 service call`` papers over all of this. A robot's
own code can't.

Run it
------
After ``ros2 run tutorial_services server`` is up::

    ros2 run tutorial_services client sit
    ros2 run tutorial_services client stand
"""

from __future__ import annotations

import sys

import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger


class PostureClient(Node):
    def __init__(self, posture: str) -> None:
        super().__init__("posture_client")
        self._client = self.create_client(Trigger, f"/posture/{posture}")
        self._posture = posture

    def call(self, timeout_s: float = 2.0) -> tuple[bool, str]:
        if not self._client.wait_for_service(timeout_sec=timeout_s):
            return False, f"service /posture/{self._posture} unreachable"
        req = Trigger.Request()
        future = self._client.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=timeout_s)
        if not future.done():
            return False, "service call timed out"
        result: Trigger.Response = future.result()
        return result.success, result.message


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    posture = (sys.argv[1] if len(sys.argv) > 1 else "sit").strip()
    if posture not in {"sit", "stand"}:
        print(f"usage: client {{sit|stand}}  (got: {posture!r})", file=sys.stderr)
        rclpy.try_shutdown()
        return

    node = PostureClient(posture)
    ok, msg = node.call()
    node.get_logger().info(f"{posture}: {'OK' if ok else 'FAIL'} — {msg}")
    node.destroy_node()
    rclpy.try_shutdown()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
