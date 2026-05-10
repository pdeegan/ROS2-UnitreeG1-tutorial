"""Lesson 04 (server): an action server that computes Fibonacci.

What this teaches
-----------------
**Actions** are the right shape for goals that take time and that a
caller might want to cancel — exactly what motion commands are.

The shape of an action:

* **Goal** — what to achieve ("walk to (x, y)").
* **Feedback** — published while the goal runs ("at (1.2, 0.4),
  remaining 0.6 m").
* **Result** — published once, when the goal finishes ("arrived").
* **Cancel** — the caller can withdraw the goal mid-flight; the
  server is responsible for stopping safely.

We use ``example_interfaces/Fibonacci`` here because it's the
canonical demo and ships with ROS 2. In lesson 09 the same pattern
drives ``g1_controller``'s real motion goals.

Run it
------
``ros2 run tutorial_actions server``

Then::

    ros2 action list
    ros2 action info /fibonacci -t
    ros2 action send_goal /fibonacci example_interfaces/action/Fibonacci '{order: 10}' --feedback
"""

from __future__ import annotations

import time

import rclpy
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.action.server import ServerGoalHandle
from rclpy.node import Node
from example_interfaces.action import Fibonacci


class FibonacciServer(Node):
    def __init__(self) -> None:
        super().__init__("fibonacci_server")
        self._action = ActionServer(
            self,
            Fibonacci,
            "/fibonacci",
            execute_callback=self._execute,
            goal_callback=self._on_goal,
            cancel_callback=self._on_cancel,
        )
        self.get_logger().info("action server up: /fibonacci")

    def _on_goal(self, goal_request: Fibonacci.Goal) -> GoalResponse:
        if goal_request.order < 1 or goal_request.order > 30:
            self.get_logger().warn(f"rejecting order={goal_request.order} (out of [1, 30])")
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def _on_cancel(self, goal_handle: ServerGoalHandle) -> CancelResponse:
        self.get_logger().info("cancel requested — accepting")
        return CancelResponse.ACCEPT

    def _execute(self, goal_handle: ServerGoalHandle) -> Fibonacci.Result:
        order = goal_handle.request.order
        self.get_logger().info(f"executing order={order}")
        feedback = Fibonacci.Feedback()
        feedback.sequence = [0, 1]
        for i in range(2, order + 1):
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                self.get_logger().info("goal canceled")
                return Fibonacci.Result()
            feedback.sequence.append(feedback.sequence[i - 1] + feedback.sequence[i - 2])
            goal_handle.publish_feedback(feedback)
            time.sleep(0.5)

        goal_handle.succeed()
        result = Fibonacci.Result()
        result.sequence = feedback.sequence
        self.get_logger().info(f"done. sequence={result.sequence}")
        return result


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = FibonacciServer()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
