"""Lesson 03 (server): a service for posture changes.

What this teaches
-----------------
Topics are for streams. Services are for **rare, atomic state
changes** with a yes/no answer: "go to damping mode", "release the
arms", "re-zero the IMU bias." A humanoid uses dozens of these.

We use ``std_srvs/Trigger`` here — the simplest possible service
type: no request fields, a ``bool success`` and ``string message``
in the response. That's enough to express most posture transitions
when the *intent* is the whole request.

This server simulates a posture-change controller: it accepts a
``Trigger`` and randomly succeeds (90%) or fails (10%) after a brief
"thinking" delay. The point is the *shape*, not the realism.

Run it
------
``ros2 run tutorial_services server``

Then in a second shell::

    ros2 service list                            # find /posture/sit
    ros2 service type /posture/sit              # std_srvs/srv/Trigger
    ros2 service call /posture/sit std_srvs/srv/Trigger
"""

from __future__ import annotations

import random
import time

import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger


class PostureServer(Node):
    def __init__(self) -> None:
        super().__init__("posture_server")
        self.declare_parameter("think_ms", 150)
        self.declare_parameter("fail_rate", 0.1)
        self._sit  = self.create_service(Trigger, "/posture/sit",  self._on_sit)
        self._stand = self.create_service(Trigger, "/posture/stand", self._on_stand)
        self.get_logger().info("services up: /posture/sit  /posture/stand")

    def _think(self) -> None:
        time.sleep(int(self.get_parameter("think_ms").value) / 1000.0)

    def _coinflip(self) -> bool:
        return random.random() > float(self.get_parameter("fail_rate").value)

    def _on_sit(self, req: Trigger.Request, resp: Trigger.Response) -> Trigger.Response:
        self.get_logger().info("posture/sit requested")
        self._think()
        if self._coinflip():
            resp.success = True
            resp.message = "sitting"
            self.get_logger().info("→ success: sitting")
        else:
            resp.success = False
            resp.message = "controller refused — IMU bias too high"
            self.get_logger().warn(f"→ failure: {resp.message}")
        return resp

    def _on_stand(self, req: Trigger.Request, resp: Trigger.Response) -> Trigger.Response:
        self.get_logger().info("posture/stand requested")
        self._think()
        if self._coinflip():
            resp.success = True
            resp.message = "standing"
            self.get_logger().info("→ success: standing")
        else:
            resp.success = False
            resp.message = "controller refused — knee torque limit"
            self.get_logger().warn(f"→ failure: {resp.message}")
        return resp


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = PostureServer()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
