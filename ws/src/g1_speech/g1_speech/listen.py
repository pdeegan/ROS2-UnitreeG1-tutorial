"""Lesson 08 (listen): VAD-gated microphone capture.

What this teaches
-----------------
Always-on audio recording into the network is a privacy footgun and
a bandwidth waste. The right shape is *voice-activity-detected*
capture: a small model says "this looks like speech," and only then
does an utterance get published.

This node uses **Silero VAD** (a tiny ONNX model, runs on CPU at
real-time) and publishes ``std_msgs/String`` to ``/g1/speech/utter``
on each detected utterance. The string is a base64-encoded WAV blob
of the captured audio — small enough to ride a ROS topic, big enough
to feed downstream ASR.

This is the entry point for a "talk to the G1" flow:

  microphone → VAD here → ASR (your choice) → intent → controller

Run it
------

::

    ros2 run g1_speech listen

Then in another shell::

    ros2 topic echo /g1/speech/utter --no-arr | head

You can also test without a microphone by setting
``G1_SPEECH_FAKE=1`` — the node will emit a stubbed utterance every
3 seconds.
"""

from __future__ import annotations

import base64
import io
import os
import threading
import wave

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

SAMPLE_RATE = 16_000
FRAME_MS = 30
FRAME_SAMPLES = SAMPLE_RATE * FRAME_MS // 1000


def fake_mode() -> bool:
    return os.environ.get("G1_SPEECH_FAKE", "0") == "1"


def _wav_bytes(pcm16: bytes, sample_rate: int = SAMPLE_RATE) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm16)
    return buf.getvalue()


class VoiceListener(Node):
    def __init__(self) -> None:
        super().__init__("voice_listener")
        self._pub = self.create_publisher(String, "/g1/speech/utter", 10)
        self._stop = threading.Event()

        if fake_mode():
            self.get_logger().info("FAKE mode — emitting a stub utterance every 3 s")
            self.create_timer(3.0, self._fake_tick)
            return

        # Real mode: lazy-import audio + VAD deps so the package imports
        # cleanly in environments where they aren't present.
        try:
            import sounddevice  # noqa: F401
        except ImportError as exc:
            self.get_logger().error(
                f"sounddevice unavailable ({exc}). Install: pip install sounddevice."
            )
            raise

        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()
        self.get_logger().info("listening (VAD-gated)")

    # ------------------------------------------------------------ fake path
    def _fake_tick(self) -> None:
        pcm = b"\x00" * FRAME_SAMPLES * 2 * 30  # ~0.9 s of silence
        msg = String()
        msg.data = base64.b64encode(_wav_bytes(pcm)).decode("ascii")
        self._pub.publish(msg)
        self.get_logger().info(f"emit fake utterance ({len(msg.data)} chars)")

    # ------------------------------------------------------------ live path
    def _capture_loop(self) -> None:
        import sounddevice as sd
        try:
            import onnxruntime as ort
        except ImportError:
            self.get_logger().warn("onnxruntime missing — falling back to energy VAD")
            ort = None  # type: ignore[assignment]

        vad = _build_silero(ort) if ort is not None else None

        speech_buf = bytearray()
        in_speech = False
        silence_frames = 0
        SILENCE_HOLDOFF = 10  # frames

        def on_frame(indata, frames, time_info, status):  # noqa: ARG001
            nonlocal in_speech, silence_frames
            if self._stop.is_set():
                raise sd.CallbackStop()
            pcm = (indata[:, 0] * 32767).astype("int16").tobytes()
            is_speech = (
                _silero_score(vad, pcm) > 0.5 if vad is not None
                else _energy_score(pcm) > 0.05
            )
            if is_speech:
                speech_buf.extend(pcm)
                in_speech = True
                silence_frames = 0
            elif in_speech:
                silence_frames += 1
                if silence_frames > SILENCE_HOLDOFF and speech_buf:
                    msg = String()
                    msg.data = base64.b64encode(_wav_bytes(bytes(speech_buf))).decode("ascii")
                    self._pub.publish(msg)
                    self.get_logger().info(f"emit utterance ({len(speech_buf)} bytes pcm)")
                    speech_buf.clear()
                    in_speech = False

        with sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            blocksize=FRAME_SAMPLES,
            callback=on_frame,
        ):
            self._stop.wait()

    def destroy_node(self) -> bool:
        self._stop.set()
        return super().destroy_node()


def _build_silero(ort):
    """Return an ort.InferenceSession with the Silero VAD onnx, or None."""
    try:
        from pathlib import Path

        candidate = Path(__file__).parent / "models" / "silero_vad.onnx"
        if not candidate.exists():
            return None
        return ort.InferenceSession(str(candidate), providers=["CPUExecutionProvider"])
    except Exception:
        return None


def _silero_score(sess, pcm16: bytes) -> float:
    import numpy as np
    audio = np.frombuffer(pcm16, dtype=np.int16).astype(np.float32) / 32768.0
    audio = audio[np.newaxis, :]
    out = sess.run(None, {"input": audio, "sr": np.array(SAMPLE_RATE, dtype=np.int64)})
    return float(out[0][0])


def _energy_score(pcm16: bytes) -> float:
    import numpy as np
    audio = np.frombuffer(pcm16, dtype=np.int16).astype(np.float32) / 32768.0
    return float((audio ** 2).mean() ** 0.5)


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = VoiceListener()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
