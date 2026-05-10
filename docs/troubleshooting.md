# Troubleshooting

The shortest path to the fix, by symptom.

## Install

### "micromamba: command not found" after install.sh

The install script writes the discovered location to
`install/.discovered.sh`. Re-source it:

```bash
source install/.discovered.sh
which $TUTORIAL_MAMBA_BIN
```

If `.discovered.sh` doesn't exist, run `bash install/01_micromamba.sh`.

### `pip install` complains about `--break-system-packages`

You're running pip outside the env. Check `which python` —
it should be `$TUTORIAL_ROS_ENV/bin/python`. If it isn't,
re-source `scripts/ros2_env.sh`.

### Install wants to download 3.5 GB

`02_robostack_ros2.sh` couldn't find your existing ROS 2 env. Check
`$HOME/micromamba/envs/`. If nothing is there, the prompt is
correct — you do need a fresh env. Confirm with
`TUTORIAL_INSTALL_ROS=1 bash install/install.sh`.

## Build (colcon)

### "colcon: command not found"

`source scripts/ros2_env.sh` wasn't run in this shell.

### "Package not found" when running an entry point

The resource marker is missing or `data_files` in `setup.py` doesn't
include it. Check:

```bash
ls ws/src/<pkg>/resource/<pkg>          # must exist as an empty file
grep -A2 data_files ws/src/<pkg>/setup.py
```

### "No module named 'humanoid_msgs'"

The interfaces package didn't build before its consumers. Force
order:

```bash
cd ws
colcon build --packages-select humanoid_msgs
source install/setup.bash
colcon build --packages-skip-build-finished
```

## Runtime (rclpy / ROS 2)

### `ros2 topic list` is empty

The daemon is dead or DDS discovery is broken:

```bash
ros2 daemon stop
ros2 daemon start
ros2 topic list
```

If still empty:

```bash
echo $ROS_DOMAIN_ID
echo $RMW_IMPLEMENTATION         # expect rmw_cyclonedds_cpp
echo $CYCLONEDDS_URI
```

A different `ROS_DOMAIN_ID` in two shells = invisible topic graphs.

### Subscriber receives nothing despite the publisher being up

QoS mismatch. Both sides must agree:

```bash
ros2 topic info /<topic> -v
```

Look at the Publishers / Subscriptions sections; if reliability or
durability differs, fix one side.

### "rclpy.spin()" never returns on Ctrl+C

You ran the node directly with `python3`, not through `ros2 run`.
The `ros2 run` wrapper installs a SIGINT handler that wakes
`spin()`. Either use `ros2 run` or add to your own `main`:

```python
import signal
signal.signal(signal.SIGINT, lambda *_: rclpy.shutdown())
```

(The lesson nodes all wrap `rclpy.spin` in `try/except KeyboardInterrupt`,
which is the lighter-weight version of the same idea.)

## G1 / bridge

### `ros2 topic hz /g1/lowstate` shows 0 Hz, no robot connected

Expected. Run with the fake emitter:

```bash
G1_BRIDGE_FAKE=1 ros2 run g1_bridge bridge
```

You should now see 50 Hz on `/g1/lowstate`.

### `/g1/lowstate` is empty but `/g1/imu` works

`humanoid_msgs` isn't built. The bridge falls back to publishing
only IMU when the custom message types aren't found. Build
`humanoid_msgs` and re-source `ws/install/setup.bash`.

### "dropped /g1/lowcmd — safety disengaged" floods the log

Working as designed. Engage safety **deliberately** before
expecting motion:

```bash
ros2 service call /g1/safety/engage std_srvs/srv/Trigger
```

If you want commands forwarded *without* engaging safety, you've
misunderstood the safety contract. Don't.

### Bridge crashes with "ChannelFactoryInitialize fail"

The interface name in `cyclonedds.xml` (or as `iface:=...` param)
doesn't exist. `ip -br addr` shows the real interface names; pick
the one on the 192.168.123.0/24 segment.

## Audio (g1_speech)

### "sounddevice unavailable" on `ros2 run g1_speech listen`

Pip extras haven't been added to the env. Run
`bash install/03_pip_layer.sh`.

### Recording works but VAD never triggers

Microphone gain is too low for the energy threshold; the Silero
model isn't downloaded so we fell back to energy VAD. Either:

- Increase mic gain in pavucontrol / Windows sound settings.
- Drop the Silero ONNX in `ws/src/g1_speech/g1_speech/models/silero_vad.onnx`.

### Piper says "voice model not found"

Download a voice:

```bash
mkdir -p ~/.cache/piper-voices
python -m piper.download_voices en_US-lessac-medium --download-dir ~/.cache/piper-voices/
```

Or set the `voice` parameter to one you have:

```bash
ros2 run g1_speech speak --ros-args -p voice:=en_US-amy-medium
```

## Lifecycle (lesson 05, controller)

### "node is not configured" after `ros2 lifecycle set ... activate`

Lifecycle transitions are linear: `unconfigured → inactive → active`.
You have to `configure` first, then `activate`. List the available
transitions:

```bash
ros2 lifecycle list /g1_controller
```

### "transition not registered" on a lifecycle command

Spelling. ROS 2's lifecycle CLI is case-sensitive on the labels but
accepts both label (`configure`) and numeric id (`1`).

## Tests

### `pytest` fails with `ModuleNotFoundError: rclpy`

You ran pytest outside the env. From the activated shell:

```bash
source scripts/ros2_env.sh
pytest tests/
```

### Tests pass locally but fail in CI

CI is missing the workspace install. Make sure CI sources
`ws/install/setup.bash` after `colcon build`.
