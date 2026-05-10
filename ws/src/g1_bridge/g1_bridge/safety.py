"""Lesson 07b: the safety latch node.

What this teaches
-----------------
The G1 bridge will not forward ``/g1/lowcmd`` to the SDK unless this
latch is engaged. The latch is a single boolean (``/g1/safety_engaged``)
published with **transient_local** durability so subscribers that
join late still see the current value.

Why a separate node? Because the operator engaging safety is a
*decision*, and decisions belong in a node the operator can see and
own. The bridge subscribes — it doesn't choose for the operator.

Run it
------

::

    ros2 run g1_bridge safety
    # then:
    ros2 service call /g1/safety/engage   std_srvs/srv/Trigger
    ros2 service call /g1/safety/release  std_srvs/srv/Trigger
    ros2 topic echo /g1/safety_engaged
"""

from __future__ import annotations

import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import Bool
from std_srvs.srv import Trigger

LATCHED_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
)


class SafetyLatch(Node):
    def __init__(self) -> None:
        super().__init__("safety_latch")
        self._engaged = False
        self._pub = self.create_publisher(Bool, "/g1/safety_engaged", LATCHED_QOS)
        self._engage_srv = self.create_service(Trigger, "/g1/safety/engage", self._on_engage)
        self._release_srv = self.create_service(Trigger, "/g1/safety/release", self._on_release)
        self._publish()
        self.get_logger().info("safety latch up (default: DISENGAGED)")

    def _publish(self) -> None:
        msg = Bool()
        msg.data = self._engaged
        self._pub.publish(msg)

    def _on_engage(self, req: Trigger.Request, resp: Trigger.Response) -> Trigger.Response:
        self._engaged = True
        self._publish()
        resp.success = True
        resp.message = "safety ENGAGED"
        self.get_logger().warn("safety ENGAGED — motion commands will be forwarded")
        return resp

    def _on_release(self, req: Trigger.Request, resp: Trigger.Response) -> Trigger.Response:
        self._engaged = False
        self._publish()
        resp.success = True
        resp.message = "safety RELEASED"
        self.get_logger().info("safety RELEASED — motion commands will be dropped")
        return resp


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = SafetyLatch()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
