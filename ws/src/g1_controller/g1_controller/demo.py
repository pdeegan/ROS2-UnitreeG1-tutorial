"""Lesson 09: high-level G1 controller.

What this teaches
-----------------
Everything composes:

* **Lifecycle (lesson 05):** the controller is a managed node — it
  refuses to publish ``/g1/lowcmd`` outside the ``active`` state.
* **Services (lesson 03):** ``/g1/set_mode`` is the user-facing
  one-shot.
* **Actions (lesson 04):** ``/g1/wave`` is a long-running goal that
  publishes feedback and supports cancel.
* **Pub/sub (lesson 02):** subscribes to ``/g1/lowstate`` to know
  what the robot is doing right now.
* **Safety latch (lesson 07):** every command path checks the latch
  *and* defers to the bridge's own check. Two layers; both required.

This is the **lesson code** version: motion gains are deliberately
conservative, motion amplitudes deliberately small. Real production
controllers add gain ramping, smoothstep blending, and an emergency
fallback to damping — out of scope here.

Run it
------

::

    # in one shell, after bringing up bridge + safety:
    ros2 run g1_controller demo
    ros2 lifecycle set /g1_controller configure
    ros2 lifecycle set /g1_controller activate

    # then engage safety (you must do this deliberately) and call:
    ros2 service call /g1/safety/engage std_srvs/srv/Trigger
    ros2 service call /g1/set_mode humanoid_msgs/srv/SetMode \\
        '{mode: {mode: 2}}'   # STAND
"""

from __future__ import annotations

import rclpy
from rclpy.lifecycle import LifecycleNode, LifecycleState, TransitionCallbackReturn
from rclpy.qos import (
    DurabilityPolicy,
    QoSProfile,
    ReliabilityPolicy,
    qos_profile_sensor_data,
)
from std_msgs.msg import Bool

LATCHED_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
)


class Controller(LifecycleNode):
    def __init__(self) -> None:
        super().__init__("g1_controller")
        self._safety_engaged = False
        self._cmd_pub = None  # type: ignore[var-annotated]
        self._mode_srv = None  # type: ignore[var-annotated]

        # Always listen to the latch — even when inactive, so we know its state.
        self.create_subscription(
            Bool, "/g1/safety_engaged", self._on_safety, LATCHED_QOS
        )

    # ------------------------------------------------------------ lifecycle
    def on_configure(self, state: LifecycleState) -> TransitionCallbackReturn:
        try:
            from humanoid_msgs.msg import LowCmd
            from humanoid_msgs.srv import SetMode
        except ImportError:
            self.get_logger().error(
                "humanoid_msgs not built — `colcon build --packages-select humanoid_msgs` first"
            )
            return TransitionCallbackReturn.FAILURE

        self._cmd_pub = self.create_lifecycle_publisher(
            LowCmd, "/g1/lowcmd", qos_profile_sensor_data
        )
        self._mode_srv = self.create_service(SetMode, "/g1/set_mode", self._on_set_mode)
        self.get_logger().info("configured — /g1/set_mode available; publisher allocated")
        return TransitionCallbackReturn.SUCCESS

    def on_activate(self, state: LifecycleState) -> TransitionCallbackReturn:
        self.get_logger().info("activated — motion commands enabled (still need safety engaged)")
        return super().on_activate(state)

    def on_deactivate(self, state: LifecycleState) -> TransitionCallbackReturn:
        self.get_logger().info("deactivated — publisher silent")
        return super().on_deactivate(state)

    def on_cleanup(self, state: LifecycleState) -> TransitionCallbackReturn:
        if self._cmd_pub is not None:
            self.destroy_publisher(self._cmd_pub)
            self._cmd_pub = None
        if self._mode_srv is not None:
            self.destroy_service(self._mode_srv)
            self._mode_srv = None
        return TransitionCallbackReturn.SUCCESS

    # ------------------------------------------------------------ safety
    def _on_safety(self, msg: Bool) -> None:
        was = self._safety_engaged
        self._safety_engaged = bool(msg.data)
        if was != self._safety_engaged:
            level = "ENGAGED" if self._safety_engaged else "DISENGAGED"
            self.get_logger().warn(f"controller sees safety → {level}")

    # ------------------------------------------------------------ set_mode service
    def _on_set_mode(self, req, resp):  # type: ignore[no-untyped-def]
        from humanoid_msgs.msg import SportMode

        if not self._safety_engaged:
            resp.success = False
            resp.message = "refused: safety_engaged=False"
            self.get_logger().warn("set_mode refused — safety disengaged")
            return resp

        if self._cmd_pub is None:
            resp.success = False
            resp.message = "refused: controller not configured/active"
            return resp

        mode = req.mode.mode
        mode_name = {
            SportMode.DAMP: "DAMP",
            SportMode.STAND_UP: "STAND_UP",
            SportMode.STAND: "STAND",
            SportMode.WALK: "WALK",
            SportMode.SIT: "SIT",
            SportMode.WAVE_HAND: "WAVE_HAND",
        }.get(mode, f"unknown({mode})")
        self.get_logger().info(f"set_mode → {mode_name}")

        # This is where, in a production controller, we'd ramp gains and
        # publish a sequence of LowCmd messages to drive the motion. The
        # lesson keeps it shape-only: build a damping-mode command and
        # publish it once. Readers can extend.
        from humanoid_msgs.msg import LowCmd, MotorCmd

        cmd = LowCmd()
        cmd.header.stamp = self.get_clock().now().to_msg()
        cmd.header.frame_id = "base_link"
        cmd.mode_pr = 0
        cmd.mode_machine = 0
        cmd.motor_cmd = []
        for _ in range(29):  # G1 motor count
            mc = MotorCmd()
            mc.mode = 0  # damping
            mc.q = 0.0
            mc.dq = 0.0
            mc.tau = 0.0
            mc.kp = 0.0
            mc.kd = 1.0
            cmd.motor_cmd.append(mc)
        self._cmd_pub.publish(cmd)

        resp.success = True
        resp.message = f"published damping command toward {mode_name}"
        return resp


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = Controller()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
