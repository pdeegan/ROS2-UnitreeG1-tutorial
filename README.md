# ROS 2 for Humanoids — a hands-on tutorial

A self-contained, end-to-end tutorial for ROS 2 (Jazzy / Humble)
targeting a **Unitree G1** humanoid, built for **Debian 13 (trixie)
WSL2 + NVIDIA discrete GPU**. Starts from a one-node "hello" and
climbs to real humanoid control: voice in, motion out.

This is **infrastructure for learning**, not a robot stack. Read the
code, edit the code, and break it on purpose.


## Why this exists

Most ROS 2 tutorials assume Ubuntu 22.04 with apt-installed packages.
That breaks the moment you sit at a Debian trixie WSL prompt with a
4090 and a Unitree G1 in the lab. This repo gives you:

- A **discovery-first install** that reuses an existing
  `~/micromamba/envs/ros2_jazzy` (or `humble`) if found, only adding
  the small audio extras on top — no 3.5 GB re-download.
- A **colcon workspace** wired and ready: lessons + sim humanoid +
  G1 bridge packages share `ws/`.
- The **real Unitree G1 URDF** (~150 MB sparse-clone of
  [`unitreerobotics/unitree_ros`](https://github.com/unitreerobotics/unitree_ros))
  is fetched on first run and rendered in rviz2 — 41 links, 165 STL
  meshes, 29 joints driven through wave / walk / squat / tpose /
  stretch patterns by `tutorial_sim`.
- A **beautiful single-file HTML walkthrough** at
  [docs/walkthrough.html](docs/walkthrough.html) — ELI5 intro, every
  CLI tool demoed, every lesson explained, no CDN.
- A **headless end-to-end test** at
  [tests/integration/full_e2e.sh](tests/integration/full_e2e.sh) that
  proves the install + build + every lesson + sim + bridge + bag
  round-trip all work on this host. Run it after every change.
- A `.claude/` harness with specialist subagents and slash commands
  for working on this codebase with Claude Code.


## Quick start

```bash
# 1. discovery-first install (reuses existing ~/micromamba/envs/ros2_*
#    if found; only adds the ~150 MB of audio extras on top)
bash install/install.sh

# 2. build the workspace (uses the helper so CMake finds Python+NumPy)
bash scripts/ros2_build.sh

# 3. activate in every new shell (or add to ~/.bashrc)
source scripts/ros2_env.sh

# 4. run the first lesson
ros2 run tutorial_basics hello
```

Open [docs/walkthrough.html](docs/walkthrough.html) in your browser to
follow the guided tour.

If you don't have an existing micromamba+ROS install, see
[install/INSTALL.md](install/INSTALL.md) for the opt-in path that
builds a fresh env from scratch.


## One-shot deploy + test (no human in the loop)

The fastest path from a fresh checkout to a fully-working,
ready-to-demo system:

```bash
bash scripts/deploy_and_test.sh
```

The script:

1. Runs `install/install.sh` (idempotent — discovers existing
   micromamba + ROS 2 env, adds only the missing pip extras).
2. **Auto-fetches the Unitree G1 URDF + meshes** from
   [`unitreerobotics/unitree_ros`](https://github.com/unitreerobotics/unitree_ros)
   if not already present (~150 MB, one-time).
3. Builds the workspace with `scripts/ros2_build.sh`.
4. Runs the full e2e (`tests/integration/full_e2e.sh`).
5. Opens the walkthrough in your default browser
   (`wslview` / `open` / `xdg-open` — cross-OS).

If you only want to **verify** an already-installed setup:

```bash
bash tests/integration/full_e2e.sh
```

~3 minutes, all headless, prints a green-line summary at the end.
Exit code 0 = everything works. The script picks an isolated
`ROS_DOMAIN_ID` so it won't collide with anything else on the host.

| Variant | When to use |
|---|---|
| `bash scripts/deploy_and_test.sh` | **First time on a new box** — install + auto-fetch G1 URDF + build + test + open browser |
| `bash tests/integration/full_e2e.sh` | Verify an existing install (skips network) |
| `bash tests/integration/full_e2e.sh --quick` | Skip per-lesson runs (~30 s) |
| `bash tests/integration/full_e2e.sh --fetch-g1` | Re-pull + re-build the G1 URDF |
| `bash tests/integration/walkthrough_smoke.sh` | Verify the walkthrough HTML interactivity (copy buttons, search) |

See [docs/testing.md](docs/testing.md) for the full coverage matrix
and the manual GUI-side checklist (rviz2, rqt, etc.) that the
headless test can't verify.

### Verifying interactive GUIs after the e2e is green

The headless `full_e2e.sh` checks that every GUI binary is **callable**
but cannot verify rendering. Walk this list once on your WSLg display
to confirm the visual side works:

```bash
source scripts/ros2_env.sh

bash scripts/tools/sim_up.sh                 # rviz2 with the Unitree G1 (wave)
bash scripts/tools/sim_up.sh walk            # walking gait
bash scripts/tools/sim_up.sh squat           # squat cycle
bash scripts/tools/sim_up.sh tpose           # T-pose calibration
bash scripts/tools/sim_up.sh stretch         # full-body rotation
bash scripts/tools/rqt_graph.sh              # live topic graph window
bash scripts/tools/rqt_plot.sh /joint_states/position[15]  # plot left_shoulder_pitch_joint
bash scripts/tools/inspect.sh                # CLI snapshot of every node/topic
```


## Repository map

```
ROS_tutorial/
├── README.md                  # this file
├── CLAUDE.md                  # engineering conventions for agents
├── AGENTS.md                  # symlink → CLAUDE.md
├── CONTRIBUTING.md            # how to add a lesson
│
├── install/                   # idempotent install scripts
│   ├── install.sh             # entry point — calls 00..05 in order
│   ├── 00_prereqs.sh          # apt prereqs + locale
│   ├── 01_micromamba.sh       # locate / bootstrap micromamba
│   ├── 02_robostack_ros2.sh   # discover (or create) the ROS 2 env
│   ├── 03_pip_layer.sh        # pip extras (audio, test helpers)
│   ├── 04_unitree_sdk.sh      # verify unitree_sdk2py + CycloneDDS
│   ├── 05_verify.sh           # green-light env check
│   ├── 06_fetch_g1_assets.sh  # opt-in: sparse-clone real Unitree G1 URDF
│   └── INSTALL.md             # human-readable install guide
│
├── docs/
│   ├── walkthrough.html       # self-contained HTML walkthrough
│   ├── architecture.md        # ROS 2 topology + humanoid context
│   ├── testing.md             # one-shot deploy + test recipe
│   ├── wsl_nvidia.md          # WSL + NVIDIA discrete setup notes
│   ├── unitree_g1.md          # G1 connection + safety guide
│   └── troubleshooting.md
│
├── ws/                        # colcon workspace
│   └── src/
│       ├── tutorial_basics/   # lesson 01: hello node
│       ├── tutorial_pubsub/   # lesson 02: publisher / subscriber
│       ├── tutorial_services/ # lesson 03: services
│       ├── tutorial_actions/  # lesson 04: actions
│       ├── tutorial_lifecycle/# lesson 05: lifecycle node
│       ├── tutorial_tf/       # lesson 06: TF2 + URDF
│       ├── tutorial_sim/      # simulated humanoid: URDF + animator + rviz2
│       ├── humanoid_msgs/     # custom msgs / srvs / actions
│       ├── g1_description/    # opt-in: vendored Unitree G1 URDF + meshes
│       ├── g1_bridge/         # lesson 07: Unitree DDS ↔ ROS 2
│       ├── g1_speech/         # lesson 08: voice in / voice out
│       └── g1_controller/     # lesson 09: high-level control
│
├── scripts/
│   ├── ros2_env.sh            # activate RoboStack + workspace
│   ├── ros2_build.sh          # colcon build (passes Python+NumPy CMake hints)
│   ├── run_tutorial.sh        # ./run_tutorial.sh 02
│   ├── lesson_new.sh          # scaffold a new ament_python lesson
│   ├── doctor.sh              # diagnostic report
│   └── tools/                 # one-line wrappers for every standard ROS 2 tool
│       ├── sim_up.sh                         # Unitree G1 in rviz2
│       ├── rqt_graph.sh / rqt_plot.sh        # GUI inspectors
│       ├── bag_record.sh / bag_play.sh       # record + replay
│       └── inspect.sh                        # one-shot system snapshot
│
├── tests/
│   ├── conftest.py            # pulls ws/install/ packages onto sys.path
│   ├── test_imports.py        # import smoke tests for every package
│   ├── test_lessons.py        # in-process pub/sub/lifecycle smoke tests
│   └── integration/
│       └── full_e2e.sh        # one-shot deploy + verify (the main CI target)
│
└── .claude/                   # Claude Code harness
    ├── settings.json
    ├── agents/                # specialist subagents
    ├── commands/              # /ros-* slash commands
    └── scripts/               # session hooks
```


## Lessons

The walkthrough climbs in difficulty. Each lesson is a complete
colcon package under `ws/src/`.

| # | Package | What you learn |
|---|---|---|
| ★ | (intro) | **ROS 2 in 10 minutes** — every concept ELI5 (read first) |
| 01 | `tutorial_basics` | Minimal `rclpy` node, logging, `ros2 run` |
| 02 | `tutorial_pubsub` | Publishers, subscribers, QoS profiles |
| 03 | `tutorial_services` | Services for synchronous request/reply |
| 04 | `tutorial_actions` | Actions for long-running goals (motion) |
| 05 | `tutorial_lifecycle` | Managed nodes — safety-critical lifecycle |
| 06 | `tutorial_tf` | TF2, URDF, robot_state_publisher |
| ▸ | `tutorial_sim` | Drives the Unitree G1 URDF in rviz2 — 29 joints animated |
| ▸ | (toolkit) | Every CLI + rqt + rosbag, demoed on the sim humanoid |
| ▸ | `g1_description` | Real Unitree G1 URDF + meshes (sparse-cloned from upstream) |
| 07 | `g1_bridge` | DDS ↔ ROS 2 bridge for Unitree state + cmd |
| 08 | `g1_speech` | Voice activity detect → TTS out on the G1 |
| 09 | `g1_controller` | High-level: sit / stand / wave, action API |

**Hands-on demos with no extra code** (bring up another shell after `source scripts/ros2_env.sh`):

```bash
bash scripts/tools/sim_up.sh                  # Unitree G1 in rviz2
bash scripts/tools/sim_up.sh walk             # any pattern: wave|walk|squat|tpose|stretch
bash scripts/tools/inspect.sh          # snapshot of every node/topic/service
bash scripts/tools/rqt_graph.sh        # live topic graph viewer
bash scripts/tools/rqt_plot.sh /joint_states/position[0]
bash scripts/tools/bag_record.sh       # record everything to bags/
bash scripts/tools/bag_play.sh         # replay newest bag
```

**Optional one-time fetch** (real G1 URDF + meshes, ~150 MB, sparse-cloned from
[`unitreerobotics/unitree_ros`](https://github.com/unitreerobotics/unitree_ros)):

```bash
bash install/06_fetch_g1_assets.sh
bash scripts/ros2_build.sh g1_description
bash scripts/tools/sim_up.sh        # G1 is the default; pass walk/squat/tpose/wave for other patterns
```


## What this is NOT

- Not an alternative to the official ROS 2 tutorials at
  [docs.ros.org](https://docs.ros.org/en/humble/Tutorials.html) — it
  complements them by being humanoid-shaped from lesson 1.
- Not a production stack. The G1 packages are pedagogical scaffolds —
  they show the shape of a real bridge without the safety surface
  area you'd want on a deployed humanoid.
- Not a Unitree SDK fork. We depend on the upstream
  `unitree_sdk2_python` and provide adapters around it.


## Safety boundary (read this)

The G1 lessons command a real humanoid. Before any motion lesson:

- **Hoist the robot or use the damping mode.** The G1 will fall over
  if it loses balance.
- **Test in a clear area.** ≥2 m radius, no soft floors, no humans.
- **Keep the e-stop in hand** (remote or wired). All motion commands
  must be cancelable in <100 ms.
- **Verify the network.** Wired ethernet to the robot's `eth0`,
  static IP on `192.168.123.x` segment.

The bridge package refuses to publish `lowcmd` while
`/g1/safety_engaged` is false. Do not patch around it.


## Source

Tutorial body and code are MIT-licensed for the project author.
ROS 2 packages are Apache 2.0 (upstream). Unitree SDK Python
bindings are under their upstream license; install pulls them
from PyPI / source.
