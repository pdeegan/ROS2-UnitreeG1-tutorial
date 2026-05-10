"""Lesson 04 (client): send a goal, stream feedback, cancel if Ctrl+C.

Exercises the full action lifecycle: send goal → goal accepted →
feedback callbacks → result, with cancel-on-signal wired up so the
server's cancel path actually gets used.
"""

from __future__ import annotations

import signal
import sys

import rclpy
from rclpy.action import ActionClient
from rclpy.action.client import ClientGoalHandle
from rclpy.node import Node
from example_interfaces.action import Fibonacci


class FibonacciClient(Node):
    def __init__(self) -> None:
        super().__init__("fibonacci_client")
        self._client = ActionClient(self, Fibonacci, "/fibonacci")
        self._goal_handle: ClientGoalHandle | None = None

    def send(self, order: int) -> int:
        if not self._client.wait_for_server(timeout_sec=3.0):
            self.get_logger().error("server not available")
            return 1

        goal = Fibonacci.Goal()
        goal.order = order
        send_future = self._client.send_goal_async(goal, feedback_callback=self._on_feedback)
        rclpy.spin_until_future_complete(self, send_future)
        self._goal_handle = send_future.result()

        if self._goal_handle is None or not self._goal_handle.accepted:
            self.get_logger().error("goal rejected by server")
            return 1
        self.get_logger().info("goal accepted, awaiting result …")

        result_future = self._goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)
        result = result_future.result().result
        self.get_logger().info(f"result: {list(result.sequence)}")
        return 0

    def cancel(self) -> None:
        if self._goal_handle is not None:
            self.get_logger().info("requesting cancel …")
            self._goal_handle.cancel_goal_async()

    def _on_feedback(self, msg) -> None:
        seq = list(msg.feedback.sequence)
        self.get_logger().info(f"partial sequence: {seq}")


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = FibonacciClient()
    order = int(sys.argv[1]) if len(sys.argv) > 1 else 8

    def on_sigint(*_: object) -> None:
        node.cancel()
    signal.signal(signal.SIGINT, on_sigint)

    rc = node.send(order)
    node.destroy_node()
    rclpy.try_shutdown()
    sys.exit(rc)


if __name__ == "__main__":
    main()
