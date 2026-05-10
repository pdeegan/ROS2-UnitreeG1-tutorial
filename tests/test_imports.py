"""Smoke tests — every package must import cleanly without a robot.

These run without sourcing the colcon install (conftest.py augments
sys.path). The g1_bridge import is the one most likely to surprise
you: it imports `unitree_sdk2py` only inside ``connect()``, so the
top-level import works even if the SDK isn't installed.
"""

from __future__ import annotations

import importlib
import os
import sys

import pytest


@pytest.mark.parametrize(
    "module",
    [
        "tutorial_basics.hello",
        "tutorial_pubsub.talker",
        "tutorial_pubsub.listener",
        "tutorial_services.posture_server",
        "tutorial_services.posture_client",
        "tutorial_actions.fibonacci_server",
        "tutorial_actions.fibonacci_client",
        "tutorial_lifecycle.lifecycle_talker",
        "tutorial_tf.static_publisher",
        "tutorial_tf.head_tracker",
        "tutorial_sim.animator",
        "tutorial_sim.twist_listener",
        "g1_bridge",
        "g1_bridge.sdk",
        "g1_bridge.safety",
        "g1_speech",
        "g1_speech.listen",
        "g1_speech.speak",
        "g1_controller",
        "g1_controller.demo",
        "g1_controller.wave_client",
    ],
)
def test_imports_clean(module: str) -> None:
    """Every package must import without throwing."""
    try:
        importlib.import_module(module)
    except ImportError as exc:
        if "rclpy" in str(exc) or "humanoid_msgs" in str(exc):
            pytest.skip(f"workspace not yet built ({exc})")
        raise


def test_g1_bridge_fake_state_shape() -> None:
    """The fake LowState emitter exposes the same field shape as the SDK record."""
    try:
        from g1_bridge.sdk import _FakeLowState
    except ImportError as exc:
        pytest.skip(f"workspace not yet built ({exc})")

    fake = _FakeLowState(tick=1, t=0.0)
    assert hasattr(fake, "tick")
    assert hasattr(fake, "imu_state")
    assert hasattr(fake, "motor_state")
    assert len(fake.motor_state) == 29
    assert hasattr(fake.imu_state, "quaternion")
    assert hasattr(fake.imu_state, "gyroscope")
    assert hasattr(fake.imu_state, "accelerometer")


def test_fake_mode_env() -> None:
    from g1_bridge.sdk import fake_mode

    os.environ.pop("G1_BRIDGE_FAKE", None)
    assert fake_mode() is False
    os.environ["G1_BRIDGE_FAKE"] = "1"
    try:
        assert fake_mode() is True
    finally:
        os.environ.pop("G1_BRIDGE_FAKE", None)


if "rclpy" not in sys.modules:
    # If we can't even import rclpy at this point, skip everything below.
    pytest.importorskip("rclpy")
