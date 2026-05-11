"""Lesson smoke tests — bring up each lesson's node briefly and verify it
publishes / subscribes what it claims to. Hardware-free.

These tests are deliberately tolerant of partial workspace state: if
``humanoid_msgs`` hasn't been built, the g1 tests skip themselves
rather than fail.
"""

from __future__ import annotations

import importlib
import time

import pytest

pytest.importorskip("rclpy")


# ---------------------------------------------------------------------------
def _spin_briefly(node, duration_s: float = 0.5) -> None:
    import rclpy
    end = time.monotonic() + duration_s
    while time.monotonic() < end:
        rclpy.spin_once(node, timeout_sec=0.05)


# ---------------------------------------------------------------------------
def test_tutorial_basics_runs() -> None:
    """Lesson 01: Hello node starts, ticks, and shuts down cleanly."""
    import rclpy
    from tutorial_basics.hello import Hello

    rclpy.init()
    try:
        node = Hello()
        _spin_briefly(node, 0.3)
        node.destroy_node()
    finally:
        rclpy.shutdown()


def test_tutorial_pubsub_round_trip() -> None:
    """Lesson 02: talker publishes JointState; listener receives at least one."""
    import rclpy
    from tutorial_pubsub.listener import JointListener
    from tutorial_pubsub.talker import FakeJointTalker

    rclpy.init()
    try:
        talker = FakeJointTalker()
        listener = JointListener()

        end = time.monotonic() + 2.0
        seen = False
        while time.monotonic() < end and not seen:
            rclpy.spin_once(talker, timeout_sec=0.02)
            rclpy.spin_once(listener, timeout_sec=0.02)
            seen = listener._count > 0  # type: ignore[attr-defined]

        assert seen, "listener never received a /joint_state message"
        talker.destroy_node()
        listener.destroy_node()
    finally:
        rclpy.shutdown()


def test_tutorial_services_call() -> None:
    """Lesson 03: posture/sit is advertised and matches the Trigger service type."""
    import rclpy
    from tutorial_services.posture_server import PostureServer

    rclpy.init()
    try:
        server = PostureServer()
        # Drain rclpy's executor briefly so service discovery completes.
        _spin_briefly(server, 0.2)

        names_and_types = server.get_service_names_and_types()
        services = dict(names_and_types)
        assert "/posture/sit" in services
        assert "/posture/stand" in services
        assert "std_srvs/srv/Trigger" in services["/posture/sit"]

        server.destroy_node()
    finally:
        rclpy.shutdown()


def test_tutorial_lifecycle_transitions() -> None:
    """Lesson 05: lifecycle node transitions through configure → activate → deactivate."""
    import rclpy
    from rclpy.lifecycle import TransitionCallbackReturn
    from tutorial_lifecycle.lifecycle_talker import LifecycleTalker

    rclpy.init()
    try:
        node = LifecycleTalker()
        # trigger_<X>() returns TransitionCallbackReturn (SUCCESS/FAILURE/ERROR).
        assert node.trigger_configure() == TransitionCallbackReturn.SUCCESS
        assert node.trigger_activate() == TransitionCallbackReturn.SUCCESS
        _spin_briefly(node, 0.3)
        assert node.trigger_deactivate() == TransitionCallbackReturn.SUCCESS
        node.destroy_node()
    finally:
        rclpy.shutdown()


def test_tutorial_tf_broadcasts() -> None:
    """Lesson 06: static_publisher emits the base_link → head_link transform."""
    import rclpy
    from tutorial_tf.static_publisher import StaticPublisher
    from tf2_ros import Buffer, TransformListener

    rclpy.init()
    try:
        publisher = StaticPublisher()
        # Static TF takes a moment to propagate; spin both nodes briefly.
        listener_node = rclpy.create_node("test_tf_listener")
        buf = Buffer()
        TransformListener(buf, listener_node)

        end = time.monotonic() + 2.0
        found = False
        while time.monotonic() < end and not found:
            rclpy.spin_once(publisher, timeout_sec=0.02)
            rclpy.spin_once(listener_node, timeout_sec=0.02)
            found = buf.can_transform("base_link", "head_link", rclpy.time.Time())

        assert found, "static transform base_link → head_link never appeared"
        listener_node.destroy_node()
        publisher.destroy_node()
    finally:
        rclpy.shutdown()


def test_tutorial_sim_animator_publishes_joints() -> None:
    """tutorial_sim animator publishes /joint_states with all 29 G1 joints."""
    import rclpy
    from sensor_msgs.msg import JointState
    from tutorial_sim.animator import G1_JOINTS, Animator

    rclpy.init()
    try:
        animator = Animator()
        listener = rclpy.create_node("test_animator_listener")
        seen: list[JointState] = []
        listener.create_subscription(JointState, "/joint_states", seen.append, 10)

        end = time.monotonic() + 2.0
        while time.monotonic() < end and not seen:
            rclpy.spin_once(animator, timeout_sec=0.02)
            rclpy.spin_once(listener, timeout_sec=0.02)

        assert seen, "no /joint_states received from the animator"
        msg = seen[0]
        assert len(G1_JOINTS) == 29, "expected 29 G1 joints"
        assert tuple(msg.name) == G1_JOINTS
        assert len(msg.position) == len(G1_JOINTS)
        listener.destroy_node()
        animator.destroy_node()
    finally:
        rclpy.shutdown()


def test_tutorial_sim_share_files_installed() -> None:
    """The G1 launch file and rviz config end up in share/tutorial_sim/."""
    import os
    from ament_index_python.packages import get_package_share_directory

    try:
        share = get_package_share_directory("tutorial_sim")
    except Exception as exc:
        pytest.skip(f"tutorial_sim not installed ({exc})")

    expected = [
        "launch/g1_sim.launch.py",
        "rviz/g1.rviz",
    ]
    for rel in expected:
        path = os.path.join(share, rel)
        assert os.path.isfile(path), f"missing share file: {rel} (looked at {path})"


# ---------------------------------------------------------------------------
def _have_humanoid_msgs() -> bool:
    try:
        importlib.import_module("humanoid_msgs.msg")
        return True
    except ImportError:
        return False


@pytest.mark.skipif(not _have_humanoid_msgs(), reason="humanoid_msgs not built")
def test_g1_bridge_fake_streams() -> None:
    """g1_bridge in FAKE mode publishes /g1/imu without a robot."""
    import os
    import rclpy
    from sensor_msgs.msg import Imu

    os.environ["G1_BRIDGE_FAKE"] = "1"
    rclpy.init()
    try:
        from g1_bridge.bridge import G1Bridge

        bridge = G1Bridge()
        listener = rclpy.create_node("test_imu_listener")
        received = []
        # Bridge publishes /g1/imu with sensor_data QoS (best-effort); the
        # listener must match or DDS marks them incompatible and routes nothing.
        from rclpy.qos import qos_profile_sensor_data
        listener.create_subscription(
            Imu, "/g1/imu", lambda m: received.append(m), qos_profile_sensor_data
        )

        end = time.monotonic() + 2.5
        while time.monotonic() < end and not received:
            rclpy.spin_once(bridge, timeout_sec=0.02)
            rclpy.spin_once(listener, timeout_sec=0.02)

        assert received, "no /g1/imu message received from fake bridge"
        listener.destroy_node()
        bridge.destroy_node()
    finally:
        rclpy.shutdown()
        os.environ.pop("G1_BRIDGE_FAKE", None)


@pytest.mark.skipif(not _have_humanoid_msgs(), reason="humanoid_msgs not built")
def test_g1_safety_latch_default_false() -> None:
    """SafetyLatch starts disengaged."""
    import rclpy
    from g1_bridge.safety import SafetyLatch

    rclpy.init()
    try:
        latch = SafetyLatch()
        assert latch._engaged is False  # type: ignore[attr-defined]
        latch.destroy_node()
    finally:
        rclpy.shutdown()
