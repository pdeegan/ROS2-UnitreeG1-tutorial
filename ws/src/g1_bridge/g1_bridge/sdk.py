"""Thin wrapper around unitree_sdk2py for the bridge.

Two important properties:

1. **Lazy import.** ``unitree_sdk2py`` is only imported when ``connect()``
   is called, so this module can be imported in test environments
   without the SDK installed.
2. **Fake mode.** If the env var ``G1_BRIDGE_FAKE=1`` is set, no SDK
   import happens at all; the wrapper emits a synthetic ``LowState_``
   at 50 Hz. This is what the smoke tests use.
"""

from __future__ import annotations

import math
import os
import threading
import time
from typing import Any, Callable

LOWSTATE_TOPIC = "rt/lowstate"
LOWCMD_TOPIC = "rt/lowcmd"


def fake_mode() -> bool:
    return os.environ.get("G1_BRIDGE_FAKE", "0") == "1"


class G1Sdk:
    """Subscribes to LowState; publishes LowCmd. SDK or fake."""

    def __init__(self, iface: str | None = None) -> None:
        self._iface = iface
        self._on_state: Callable[[Any], None] | None = None
        self._state_sub = None  # SDK ChannelSubscriber, or None in fake mode
        self._cmd_pub = None    # SDK ChannelPublisher, or None in fake mode
        self._fake_thread: threading.Thread | None = None
        self._stop = threading.Event()

    # ------------------------------------------------------------------ connect
    def connect(self) -> None:
        if fake_mode():
            self._fake_thread = threading.Thread(target=self._fake_loop, daemon=True)
            self._fake_thread.start()
            return

        from unitree_sdk2py.core.channel import (
            ChannelFactoryInitialize,
            ChannelPublisher,
            ChannelSubscriber,
        )
        from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_, LowState_

        if self._iface:
            ChannelFactoryInitialize(0, self._iface)
        else:
            ChannelFactoryInitialize(0)

        self._state_sub = ChannelSubscriber(LOWSTATE_TOPIC, LowState_)
        self._state_sub.Init(self._on_sdk_state, 10)

        self._cmd_pub = ChannelPublisher(LOWCMD_TOPIC, LowCmd_)
        self._cmd_pub.Init()

    # ------------------------------------------------------------------ close
    def close(self) -> None:
        self._stop.set()
        if self._fake_thread is not None:
            self._fake_thread.join(timeout=1.0)
        if self._state_sub is not None:
            try:
                self._state_sub.Close()
            except Exception:
                pass
        if self._cmd_pub is not None:
            try:
                self._cmd_pub.Close()
            except Exception:
                pass

    # ------------------------------------------------------------------ callbacks
    def on_state(self, callback: Callable[[Any], None]) -> None:
        self._on_state = callback

    def _on_sdk_state(self, msg: Any) -> None:
        if self._on_state is not None:
            self._on_state(msg)

    # ------------------------------------------------------------------ publish
    def publish_cmd(self, cmd: Any) -> None:
        if fake_mode() or self._cmd_pub is None:
            return
        self._cmd_pub.Write(cmd)

    # ------------------------------------------------------------------ fake mode
    def _fake_loop(self) -> None:
        """Emit a synthetic LowState_-shaped record at 50 Hz."""
        tick = 0
        period = 1.0 / 50.0
        while not self._stop.is_set():
            tick += 1
            fake_state = _FakeLowState(tick=tick, t=tick * period)
            if self._on_state is not None:
                self._on_state(fake_state)
            time.sleep(period)


class _FakeMotor:
    __slots__ = ("mode", "q", "dq", "ddq", "tau_est", "temperature", "vol", "sensor")

    def __init__(self, q: float) -> None:
        self.mode = 1
        self.q = q
        self.dq = 0.0
        self.ddq = 0.0
        self.tau_est = 0.0
        self.temperature = 35.0
        self.vol = 24.0
        self.sensor = 0


class _FakeImu:
    __slots__ = ("quaternion", "gyroscope", "accelerometer", "rpy", "temperature")

    def __init__(self, t: float) -> None:
        self.quaternion = (1.0, 0.0, 0.0, 0.0)
        self.gyroscope = (0.0, 0.0, 0.0)
        self.accelerometer = (0.0, 0.0, 9.81)
        self.rpy = (0.0, 0.0, 0.0)
        self.temperature = 40.0


class _FakeLowState:
    """Quacks like ``unitree_sdk2py.idl.unitree_hg.msg.dds_.LowState_``."""

    __slots__ = (
        "version", "mode_pr", "mode_machine", "tick",
        "imu_state", "motor_state", "wireless_remote",
        "reserve", "crc", "power_v", "power_a",
    )

    def __init__(self, tick: int, t: float) -> None:
        self.version = (1, 0)
        self.mode_pr = 0
        self.mode_machine = 0
        self.tick = tick
        self.imu_state = _FakeImu(t)
        # 29 motors on G1 (waist + legs + arms + head); we just give a sine wave
        self.motor_state = [_FakeMotor(0.1 * math.sin(t + i * 0.3)) for i in range(29)]
        self.wireless_remote = bytes(40)
        self.reserve = (0, 0, 0, 0)
        self.crc = 0
        self.power_v = 47.3
        self.power_a = 1.8
