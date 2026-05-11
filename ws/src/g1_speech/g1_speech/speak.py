"""Lesson 08 (speak): a service that synthesizes speech and plays it.

What this teaches
-----------------
For a humanoid the "speak" action is a *service*, not a topic. The
operator wants one of:

  * "say this and tell me when you've finished saying it"
  * "say this *now*, preempting whatever you were saying"

A topic gives you neither. A service gives you the first; an action
gives you the second. We do the service here — the simpler case.

Backed by **Piper**, an offline TTS that runs on CPU at faster than
real-time. The model files are not bundled; on first use the node
downloads (or expects) a voice in ``~/.cache/piper-voices/``.

Run it
------

::

    ros2 run g1_speech speak

Then::

    ros2 service call /g1/speech/say std_srvs/srv/Trigger '{}'   # smoke
    # or with a real message type:
    ros2 service call /g1/speech/say_text humanoid_msgs/srv/SetMode '{...}'

Without piper installed, the node falls back to writing a WAV to
``/tmp/g1_speak_<ts>.wav`` and logging the path.
"""

from __future__ import annotations

import os
import tempfile
import time
import wave
from pathlib import Path

import rclpy
from rclpy.node import Node
from std_srvs.srv import Trigger


class Speaker(Node):
    def __init__(self) -> None:
        super().__init__("speaker")
        self.declare_parameter("voice", "en_US-lessac-medium")
        self.declare_parameter("text", "Hello. I am the G1. How can I help?")
        self._svc = self.create_service(Trigger, "/g1/speech/say", self._on_say)
        self._piper = self._init_piper()
        backend = "piper" if self._piper is not None else "wav-stub"
        self.get_logger().info(f"speaker up (backend={backend})")

    def _init_piper(self):
        try:
            from piper.voice import PiperVoice  # type: ignore[import-not-found]
        except ImportError:
            self.get_logger().warn("piper-tts not installed; using wav-stub backend")
            return None
        voice_name = str(self.get_parameter("voice").value)
        voice_path = Path.home() / ".cache" / "piper-voices" / f"{voice_name}.onnx"
        if not voice_path.exists():
            self.get_logger().warn(
                f"voice model not found at {voice_path}; "
                "download with: python -m piper.download_voices "
                f"{voice_name} --download-dir ~/.cache/piper-voices/"
            )
            return None
        try:
            return PiperVoice.load(str(voice_path))
        except Exception as exc:
            self.get_logger().warn(f"failed to load piper voice: {exc}")
            return None

    def _on_say(self, req: Trigger.Request, resp: Trigger.Response) -> Trigger.Response:
        text = str(self.get_parameter("text").value)
        self.get_logger().info(f"saying: {text!r}")
        path = self._synthesize_to_wav(text)
        if path is None:
            resp.success = False
            resp.message = "no TTS backend available"
            return resp
        self._play(path)
        resp.success = True
        resp.message = f"spoke {text!r} (wav at {path})"
        return resp

    def _synthesize_to_wav(self, text: str) -> str | None:
        if self._piper is None:
            # Write a silent placeholder so callers can verify the path.
            ts = int(time.time())
            path = f"/tmp/g1_speak_{ts}.wav"
            with wave.open(path, "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(22_050)
                w.writeframes(b"\x00\x00" * 22_050)  # 1s of silence
            return path

        fd, path = tempfile.mkstemp(suffix=".wav", prefix="g1_speak_")
        os.close(fd)
        # piper's synthesize_wav writes through a wave.Wave_write handle,
        # not a raw binary file. Calling it with a plain open(..., "wb")
        # silently produces a zero-byte file.
        with wave.open(path, "wb") as w:
            self._piper.synthesize_wav(text, w)
        return path

    def _play(self, wav_path: str) -> None:
        # sd.wait() blocks the executor for the full clip length, which
        # makes the node unresponsive to shutdown signals and any other
        # service call during playback. Start playback and return; the
        # service caller gets success as soon as the WAV is queued.
        try:
            import sounddevice as sd
            import soundfile as sf
            data, sr = sf.read(wav_path)
            sd.play(data, sr)  # non-blocking; sounddevice's PortAudio stream owns the clip
        except Exception as exc:
            self.get_logger().info(f"audio playback skipped ({exc}); wav saved to {wav_path}")


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = Speaker()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, rclpy.executors.ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()
