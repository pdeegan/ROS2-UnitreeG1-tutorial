# Testing — deploy and verify the whole tutorial

This page is the recipe for going from a fresh checkout to a fully
verified, runnable tutorial. Designed for **Debian 13 (trixie) WSL2 +
NVIDIA discrete**, but works on any Linux + Python 3.11/3.12 host.

## TL;DR — one command to test everything

```bash
bash tests/integration/full_e2e.sh
```

Runs: install discovery → colcon build → pytest → every lesson briefly
→ sim humanoid launch → G1 bridge in fake mode → safety latch
propagation → rosbag record + replay → GUI tool sanity. ~3 minutes,
all headless, no human in the loop.

If you also want the real Unitree G1 URDF (~150 MB download from
GitHub) verified end-to-end:

```bash
bash tests/integration/full_e2e.sh --fetch-g1
```

Exit code 0 = everything works. Non-zero = something is wrong; the
script lists exactly which checks failed and where the per-step logs
live (`/tmp/e2e_*.log`).


## What gets tested, and why

### Phase 1 — install discovery (~10 s)

Runs `install/01_micromamba.sh` → `05_verify.sh` in order. **None of
these download multi-GB packages on a healthy host** — they detect
the existing micromamba + ROS 2 env and skip. The pip layer adds
~150 MB of audio extras only if missing.

This phase catches: stale `install/.discovered.sh`, missing rclpy,
broken `ros2` CLI, missing audio packages, missing `unitree_sdk2py`,
missing CycloneDDS profile.

### Phase 1b — G1 asset fetch (opt-in, ~150 MB)

Only runs when you pass `--fetch-g1` or when
`ws/src/g1_description/` already exists. Sparse-clones
[`unitreerobotics/unitree_ros`](https://github.com/unitreerobotics/unitree_ros)
on master, picks just the `robots/g1_description/` subtree, wraps it
as a colcon package. Idempotent.

### Phase 2 — colcon build (~10 s incremental, ~60 s clean)

Builds every package in the workspace via `bash scripts/ros2_build.sh`
(which passes the Python + NumPy CMake hints needed by RoboStack
Jazzy's CMake 4.2). Catches: missing `package.xml` / `setup.py`
fields, type errors caught by ament's Python build, broken xacro,
missing C++ deps, msg/srv/action generation failures.

### Phase 3 — pytest (~3 s)

Runs `tests/test_imports.py` + `tests/test_lessons.py`. ~32 tests:
every package imports without a robot connected, every lesson's main
node starts and shuts down cleanly, the bridge in fake mode emits
state, the lifecycle node transitions, the safety latch defaults to
disengaged, the sim animator publishes the right joint names.

### Phase 4 — every lesson runs (~25 s)

Brings each lesson's primary entry point up under a 4-second
timeout, then verifies the expected topic appears on the graph
within 8 seconds. Skipped under `--quick`.

| Lesson | Expected topic |
|---|---|
| 01 `tutorial_basics` | `/rosout` |
| 02 `tutorial_pubsub talker` | `/joint_state` |
| 02 `tutorial_pubsub listener` | (just doesn't crash) |
| 03 `tutorial_services server` | `/rosout` |
| 04 `tutorial_actions server` | (just doesn't crash) |
| 05 `tutorial_lifecycle` | (just doesn't crash) |
| 06 `tutorial_tf static_publisher` | `/tf_static` |
| 06 `tutorial_tf head_tracker` | `/tf` |

### Phase 5 — sim humanoid launches (~10 s)

`ros2 launch tutorial_sim g1_sim.launch.py rviz:=false` brings up:
`robot_state_publisher` + `joint_animator` (rviz omitted in test mode).
Verifies `/joint_states` streams, then exercises `ros2 param get/set`
to swap the animation pattern from `wave` to `walk`. Requires the G1
URDF to be built (`bash install/06_fetch_g1_assets.sh` then
`bash scripts/ros2_build.sh g1_description`); the phase skips
otherwise.

### Phase 6 — G1 bridge in fake mode (~5 s)

Brings up `g1_bridge` (with `G1_BRIDGE_FAKE=1`) + `safety_latch`.
Verifies all four expected topics appear (`/g1/imu`, `/g1/lowstate`,
`/g1/lowcmd`, `/g1/safety_engaged`), then calls
`/g1/safety/engage` and verifies the bridge logs the latch
transition (proves the latch propagates structurally).

### Phase 7 — rosbag record + replay (~10 s)

Brings up the sim, records 3 seconds of `/joint_states` + `/tf`,
verifies `metadata.yaml` + non-zero message count, kills the
producer, replays the bag, verifies the topic re-appears. Catches
rosbag2 storage plugin issues (mcap needs the `rosbag2_storage_mcap`
plugin in the env).

### Phase 8 — GUI tools sanity (~2 s)

Verifies `rviz2`, `rqt_graph`, `rqt_plot`, `tf2_echo`, and `gz`
binaries are available. Doesn't try to open a window (would hang
headless). If you're on a real desktop or WSLg, manually verify the
GUI side with `bash scripts/tools/sim_up.sh`.


## Running by hand

If something fails, isolate it. Each script is independent:

```bash
# install plumbing only
bash install/install.sh

# build only
bash scripts/ros2_build.sh                    # whole workspace
bash scripts/ros2_build.sh humanoid_msgs      # one package

# unit tests only
source scripts/ros2_env.sh
pytest tests/test_imports.py tests/test_lessons.py -v

# diagnostic dump (env, GPU, network)
bash scripts/doctor.sh
```

For the GUI half — what the e2e can't verify because it's headless —
walk this list manually after the e2e is green:

```bash
source scripts/ros2_env.sh

# 1. Real Unitree G1 in rviz (default pattern: wave)
bash install/06_fetch_g1_assets.sh         # one-time, ~150 MB
bash scripts/ros2_build.sh g1_description  # one-time
bash scripts/tools/sim_up.sh
#   should see: rviz2 window with the Unitree G1, right arm waving

# 2. Other animation patterns
bash scripts/tools/sim_up.sh walk          # walking gait
bash scripts/tools/sim_up.sh squat         # squat cycle
bash scripts/tools/sim_up.sh tpose         # calibration pose
bash scripts/tools/sim_up.sh stretch       # full-body rotation

# 3. The live topic graph
bash scripts/tools/rqt_graph.sh
#   should see: rqt window, nodes-and-edges diagram

# 4. Live numeric plot
bash scripts/tools/rqt_plot.sh /joint_states/position[0]
#   should see: scrolling sine wave

# 5. Snapshot the live system
bash scripts/tools/inspect.sh
#   should see: tabular output of every node/topic/service/param/rate
```


## CI — running this in GitHub Actions

The e2e is designed to run inside a CI runner. Skeleton:

```yaml
# .github/workflows/test.yml
name: e2e
on: [push, pull_request]
jobs:
  e2e:
    runs-on: ubuntu-latest
    container: ubuntu:22.04
    steps:
      - uses: actions/checkout@v4
      - run: |
          apt-get update && apt-get install -y curl bzip2 git build-essential
          bash install/00_prereqs.sh
          TUTORIAL_INSTALL_ROS=1 bash install/install.sh
      - run: bash tests/integration/full_e2e.sh --skip-fetch --quick
      # The headless full_e2e covers everything except GUI rendering.
```

In CI you'd typically pass `--quick` (skip the longer per-lesson
timeout block) and `--skip-fetch` (don't pull 150 MB on every PR).
For nightlies, drop `--quick` and add `--fetch-g1`.


## When the e2e fails

The script halts at the first build failure (because nothing else
will work) and continues past unit-test / integration failures
(because they're independent). Look at:

1. The summary at the bottom — lists every failed check by name.
2. `/tmp/e2e_<step>.log` — full stdout/stderr of the failing step.
3. The "last 25 lines" preview the script prints inline.

Common patterns:

| Symptom | Likely cause | Fix |
|---|---|---|
| `colcon build` fails | Setuptools >= 80 dropped `develop --editable`, or CMake can't find Python | Use `bash scripts/ros2_build.sh` (passes the right hints) |
| `pytest` hangs in DDS init | Stale daemon from prior run | The e2e auto-cleans; if running by hand, `ros2 daemon stop` |
| `Failed to find a free participant index` | Other shells using the same `ROS_DOMAIN_ID` | The e2e picks a random domain; for manual runs `export ROS_DOMAIN_ID=99` |
| `rosbag record` produces no metadata.yaml | mcap storage plugin missing | `pip install rosbag2-storage-mcap` (already in env on a healthy install) |
| `rviz2 black window` | `/dev/dxg` missing or WSLg not running | `wsl --update` from PowerShell, reopen the shell |

If the e2e fails on a fresh checkout but the install scripts pass,
the most likely cause is a leftover ROS daemon or rosbag process
from a prior debugging session. Kill them with:

```bash
pkill -9 -f 'tutorial_|joint_animator|g1_bridge|rosbag'
ros2 daemon stop
```


## Coverage summary

- **Install path** — every script under `install/`.
- **Build path** — every package under `ws/src/`.
- **Code path** — every package's main entry point + every test in `tests/`.
- **Topic graph** — every expected topic on the bridge + sim + lessons.
- **Service graph** — at least one service call on the bridge (`/g1/safety/engage`).
- **Parameter API** — `ros2 param get/set` on `/joint_animator pattern`.
- **Lifecycle API** — node transitions through configure → activate → deactivate.
- **Action API** — server starts cleanly under timeout (smoke).
- **rosbag2** — record + info + replay round-trip.
- **GUI tools** — binaries present (cannot verify rendering headless).

What is **not** tested:
- The real Unitree G1 (no hardware in the loop on this host).
- ML-accelerated paths (Silero VAD with CUDA, Piper with CUDA).
- Anything requiring a microphone (`g1_speech.listen` real-mode).
- The walk-to-pose action against a physics sim (Gazebo wiring is opt-in).

For those, the manual checklist in the "Running by hand" section is
the recipe.
