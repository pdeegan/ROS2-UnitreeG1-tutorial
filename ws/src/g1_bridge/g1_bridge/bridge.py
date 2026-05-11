"""Lesson 07: the Unitree G1 ↔ ROS 2 bridge.

What this teaches
-----------------
Two protocol stacks (Unitree's DDS topics, ROS 2's RMW) meet in one
process. The bridge translates messages in both directions and is
the *only* place where the safety latch is enforced — every motion
command path eventually narrows here.

The shape of the bridge:

* Subscribes to the SDK's ``rt/lowstate`` (Unitree IDL) →
  republishes as ``/g1/lowstate`` and ``/g1/imu``.
* Subscribes to ROS ``/g1/lowcmd`` → forwards to ``rt/lowcmd``
  **only if** the latch (``/g1/safety_engaged``) is True.
* On startup the latch is False; the bridge logs a warning per
  rejected command so operators see them.

Run it
------

::

    # without a real robot — uses the fake LowState emitter:
    G1_BRIDGE_FAKE=1 ros2 run g1_bridge bridge

    # second shell:
    ros2 run g1_bridge safety
    ros2 topic echo /g1/lowstate                  # should stream at ~50 Hz
    ros2 topic echo /g1/imu

    # with a real robot, after connecting wired ethernet:
    export CYCLONEDDS_URI=file://$PWD/install/cyclonedds.xml
    ros2 run g1_bridge bridge --ros-args -p iface:=eth0
"""

from __future__ import annotations

import rclpy
from rclpy.node import Node
from rclpy.qos import (
    DurabilityPolicy,
    QoSProfile,
    ReliabilityPolicy,
    qos_profile_sensor_data,
)
from sensor_msgs.msg import Imu
from std_msgs.msg import Bool

from g1_bridge.sdk import G1Sdk, fake_mode

LATCHED_QOS = QoSProfile(
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
)


class G1Bridge(Node):
    def __init__(self) -> None:
        super().__init__("g1_bridge")
        self.declare_parameter("iface", "")
        iface = str(self.get_parameter("iface").value) or None

        self._safety_engaged = False
        self._dropped = 0

        try:
            from humanoid_msgs.msg import LowCmd, LowState
        except ImportError as exc:
            # Refuse to start in degraded mode without flagging it loud and
            # repeatedly. A reader who forgot `colcon build --packages-select
            # humanoid_msgs` will otherwise see "bridge up" and spend hours
            # wondering why their /g1/lowcmd publish has no effect.
            self.get_logger().error(
                "humanoid_msgs is not built — the bridge cannot accept "
                "/g1/lowcmd or publish /g1/lowstate. Build it first:"
            )
            self.get_logger().error(
                "  bash scripts/ros2_build.sh humanoid_msgs"
            )
            self.get_logger().error(f"(import error was: {exc})")
            LowState = None
            LowCmd = None

        self._state_pub = (
            self.create_publisher(LowState, "/g1/lowstate", qos_profile_sensor_data)
            if LowState is not None
            else None
        )
        self._imu_pub = self.create_publisher(Imu, "/g1/imu", qos_profile_sensor_data)

        if LowCmd is not None:
            self._cmd_sub = self.create_subscription(
                LowCmd, "/g1/lowcmd", self._on_cmd, qos_profile_sensor_data
            )
        else:
            self._cmd_sub = None
            # Periodic loud reminder so users notice if they leave the bridge
            # running in this degraded state.
            self._warn_timer = self.create_timer(10.0, self._warn_no_lowcmd)

    def _warn_no_lowcmd(self) -> None:
        self.get_logger().warn(
            "humanoid_msgs missing — /g1/lowcmd subscription is NOT active; "
            "no command will reach the robot. Build humanoid_msgs and restart."
        )

        self._safety_sub = self.create_subscription(
            Bool, "/g1/safety_engaged", self._on_safety, LATCHED_QOS
        )

        self._sdk = G1Sdk(iface=iface)
        self._sdk.on_state(self._on_sdk_state)
        self._sdk.connect()
        mode = "FAKE" if fake_mode() else "LIVE"
        self.get_logger().info(
            f"bridge up [{mode}] iface={iface or '<auto>'} — safety DISENGAGED"
        )

    # ------------------------------------------------------------ state path
    def _on_sdk_state(self, lowstate) -> None:
        # IMU — always publish, no humanoid_msgs dependency.
        imu = Imu()
        imu.header.stamp = self.get_clock().now().to_msg()
        imu.header.frame_id = "imu_link"
        q = lowstate.imu_state.quaternion
        imu.orientation.w, imu.orientation.x, imu.orientation.y, imu.orientation.z = q
        gx, gy, gz = lowstate.imu_state.gyroscope
        imu.angular_velocity.x, imu.angular_velocity.y, imu.angular_velocity.z = gx, gy, gz
        ax, ay, az = lowstate.imu_state.accelerometer
        imu.linear_acceleration.x, imu.linear_acceleration.y, imu.linear_acceleration.z = ax, ay, az
        self._imu_pub.publish(imu)

        # Full LowState — only if humanoid_msgs is built.
        if self._state_pub is None:
            return
        from humanoid_msgs.msg import LowState, MotorState

        out = LowState()
        out.header.stamp = imu.header.stamp
        out.header.frame_id = "base_link"
        out.tick = int(getattr(lowstate, "tick", 0))
        out.mode_pr = int(getattr(lowstate, "mode_pr", 0))
        out.mode_machine = int(getattr(lowstate, "mode_machine", 0))
        out.imu = imu
        out.motor_state = []
        for m in lowstate.motor_state:
            ms = MotorState()
            ms.mode = int(getattr(m, "mode", 0))
            ms.q = float(getattr(m, "q", 0.0))
            ms.dq = float(getattr(m, "dq", 0.0))
            ms.ddq = float(getattr(m, "ddq", 0.0))
            ms.tau_est = float(getattr(m, "tau_est", 0.0))
            ms.temperature = float(getattr(m, "temperature", 0.0))
            ms.vol = float(getattr(m, "vol", 0.0))
            ms.sensor_id = int(getattr(m, "sensor", 0))
            out.motor_state.append(ms)
        out.battery_voltage = float(getattr(lowstate, "power_v", 0.0))
        out.battery_current = float(getattr(lowstate, "power_a", 0.0))
        self._state_pub.publish(out)

    # ------------------------------------------------------------ command path
    def _on_safety(self, msg: Bool) -> None:
        was = self._safety_engaged
        self._safety_engaged = bool(msg.data)
        if was != self._safety_engaged:
            self.get_logger().warn(
                f"safety latch → {'ENGAGED' if self._safety_engaged else 'RELEASED'}"
            )

    def _on_cmd(self, msg) -> None:
        # **Structural** safety gate. Move this check and you have a bug.
        if not self._safety_engaged:
            self._dropped += 1
            if self._dropped % 50 == 1:
                self.get_logger().warn(
                    f"dropped /g1/lowcmd — safety disengaged ({self._dropped} total)"
                )
            return

        if fake_mode():
            # No real robot to write to; just log a heartbeat occasionally.
            return

        from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_, MotorCmd_

        out = LowCmd_()
        out.mode_pr = int(msg.mode_pr)
        out.mode_machine = int(msg.mode_machine)
        out.motor_cmd = []
        for m in msg.motor_cmd:
            mc = MotorCmd_()
            mc.mode = int(m.mode)
            mc.q = float(m.q)
            mc.dq = float(m.dq)
            mc.tau = float(m.tau)
            mc.kp = float(m.kp)
            mc.kd = float(m.kd)
            out.motor_cmd.append(mc)
        self._sdk.publish_cmd(out)

    # ------------------------------------------------------------ shutdown
    def destroy_node(self) -> bool:
        try:
            self._sdk.close()
        except Exception:
            pass
        return super().destroy_node()


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = G1Bridge()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
