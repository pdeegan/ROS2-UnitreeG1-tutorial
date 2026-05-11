# Install guide — Debian / Ubuntu / macOS (incl. WSL2)

This guide explains *why* the install is shaped the way it is so you can
debug it when it bites.

## Supported platforms

| Platform | Status | Package manager | Notes |
|---|---|---|---|
| Debian 13 (trixie) WSL2 | ✅ reference (35/35 e2e green) | apt | The dev box this was built on. NVIDIA passthrough verified. |
| Debian 12 (bookworm) | ✅ should work | apt | Same install path as trixie. |
| Ubuntu 22.04 / 24.04 | ✅ should work | apt | RoboStack works; native `apt install ros-jazzy-desktop` is also a valid alternative. |
| Ubuntu 22.04 / 24.04 WSL2 | ✅ should work | apt | Same as native Ubuntu plus `/dev/dxg` GPU passthrough. |
| Fedora / RHEL / Rocky | ⚠️ untested but covered | dnf | `00_prereqs.sh` handles dnf; rest is OS-agnostic via micromamba. |
| macOS Apple Silicon (arm64) | ⚠️ supported, untested on this build | brew | RoboStack ships `osx-arm64` binaries. CUDA paths skip; rviz2 uses native Qt. |
| macOS Intel (x86_64) | ⚠️ supported, untested on this build | brew | RoboStack ships `osx-64` binaries. |

`install/_os.sh` auto-detects the platform; every install script branches accordingly.
On macOS you need [Homebrew](https://brew.sh) before running `00_prereqs.sh`.

---

## The discovery-first model

The install scripts do not assume a fresh machine. They probe, in order,
for the things they need; only what's missing gets installed. The
canonical search order:

| Component | Probe order | Action if absent |
|---|---|---|
| `micromamba` | `~/.local/bin/micromamba` → `~/micromamba/bin/micromamba` → `$PATH` → repo-local | Bootstrap into `./.micromamba/` |
| ROS 2 env | `~/micromamba/envs/ros2_jazzy` → `ros2_humble` → `ros2` → `./.env_ros2` | **Refuse**, unless `TUTORIAL_INSTALL_ROS=1` — fresh env is ~3.5 GB |
| pip extras (audio) | Per-module probe | `pip install` only the missing ones |
| `unitree_sdk2py` | `import unitree_sdk2py` | **Print** install command; do not auto-install |
| CycloneDDS profile | `install/cyclonedds.xml` | Write default; do not overwrite |

Why so cautious? Disk is finite. On a dev box that already runs the
Master Control Agent stack, ROS 2 Jazzy is already in
`~/micromamba/envs/ros2_jazzy/`. Re-installing it would burn 3.5 GB
and create a divergent env. We reuse what's there.

The discovered paths are persisted to `install/.discovered.sh` so
later steps and `scripts/ros2_env.sh` agree on what they're talking
about. Delete that file to force re-discovery.

---

## ROS 2 distro: Jazzy vs Humble

If the host already has a working ROS 2 env, the tutorial uses it
regardless of distro. Two distros are validated:

- **Jazzy** (May 2024, LTS through May 2029, Python 3.12 — RoboStack
  ships it on 3.11/3.12). This is what's installed on the target
  machine and what the lessons primarily target.
- **Humble** (May 2022, LTS through May 2027, Python 3.10/3.11). Also
  works — every lesson uses APIs available in Humble.

Differences between Jazzy and Humble that matter for these lessons:

- `rclpy.node.Node.declare_parameter` — identical.
- Launch files (`launch_ros`) — identical for the simple cases used here.
- `lifecycle` API — identical.
- TF2 — identical (`tf2_ros`, `tf2_geometry_msgs`).
- Action API — identical.

If you write something that *does* care about the distro, gate on
`os.environ['ROS_DISTRO']`.

---

## What each install script does

| Script | Purpose | Skips if |
|---|---|---|
| `00_prereqs.sh` | apt prereqs + locale + WSL/NVIDIA sanity print | Each apt pkg already present |
| `01_micromamba.sh` | Locate micromamba; bootstrap only if absent | Found in any candidate location |
| `02_robostack_ros2.sh` | Locate ROS 2 env; refuse to create unless `TUTORIAL_INSTALL_ROS=1` | Found in any candidate location |
| `03_pip_layer.sh` | Install only the missing pip extras (audio + test helpers) | Each module imports already |
| `04_unitree_sdk.sh` | Verify `unitree_sdk2py` + write CycloneDDS profile | Profile exists |
| `05_verify.sh` | Green-light check | (always runs) |

All five are idempotent. `bash install/install.sh` is safe to re-run.

---

## WSL2 + NVIDIA discrete (RTX 4090)

Three things must be true for the GPU to work in WSL2:

1. **Windows NVIDIA driver ≥ 535** installed on the host. WSL gets its
   CUDA stack from Windows, not Linux.
2. **`wsl --update`** has been run recently. The WSL kernel ships the
   `/dev/dxg` device that exposes the GPU to Linux processes.
3. **No `nvidia-*` apt packages installed inside WSL.** Installing
   Linux NVIDIA drivers inside WSL is the classic footgun — it
   overwrites the WSL shim and you lose GPU access. The
   `nvidia-smi` you see in the prompt comes from Windows via shim.

If `nvidia-smi` works in your shell and `/dev/dxg` exists, you're
good. The lessons here don't need CUDA; the optional ML accelerations
(ONNX VAD, future SLM) auto-detect it. To enable GPU for ONNX, swap
`onnxruntime` for `onnxruntime-gpu` in `requirements.txt` and re-run
`bash install/03_pip_layer.sh`.

---

## Network: connecting to a Unitree G1

The G1 expects a wired ethernet on the `192.168.123.0/24` segment.

WSL2's default NAT mode hides the host adapters; for real-robot work
you need **mirrored networking** or a USB-Ethernet passthrough so
WSL's Linux side can see the robot's subnet. In `~/.wslconfig`:

```ini
[wsl2]
networkingMode=mirrored
```

After editing, `wsl --shutdown` and reopen the shell. Verify with
`ip -br addr` — you should see the host's ethernet interface.

Then set the CycloneDDS profile to that interface:

```bash
export CYCLONEDDS_URI=file:///path/to/ROS_tutorial/install/cyclonedds.xml
```

Edit `cyclonedds.xml` and change `name="eth0"` to your interface
name.

---

## Disk footprint (with reuse)

| Component | First-time cost | Reuse cost |
|---|---|---|
| micromamba | 0 (reused from `~/.local/bin/`) | 0 |
| ROS 2 env | 0 (reused from `~/micromamba/envs/ros2_jazzy/`) | 0 |
| pip extras (audio + test) | ~150 MB | 0 |
| Workspace build artifacts | grows with lessons; ~500 MB cap | re-build only changed packages |

**Net cost when reusing the existing env: ~150 MB** for audio extras
plus the workspace build (delta from current state).

If you actually need a fresh env (no existing one, or you want a
clean dev env separate from MCA):

```bash
TUTORIAL_INSTALL_ROS=1 bash install/install.sh
```

This downloads RoboStack `ros-humble-desktop` (~3.5 GB) into
`~/micromamba/envs/ros2_humble/`.

---

## Uninstall

If we created a new env (you opted in via `TUTORIAL_INSTALL_ROS=1`):

```bash
~/.local/bin/micromamba env remove -p ~/micromamba/envs/ros2_humble
```

If we only added pip extras to your existing env — there's no clean
uninstall short of `pip uninstall` per package; the extras are small.

Workspace artifacts:

```bash
rm -rf ws/build ws/install ws/log install/.discovered.sh
```

---

## Common gotchas

- **"colcon: command not found"** — you didn't `source scripts/ros2_env.sh`.
- **"ros2 daemon" hangs on shutdown** — `ros2 daemon stop` then retry. WSL2 + multicast leaves the daemon orphaned occasionally.
- **rviz2 black window** — `/dev/dxg` missing or WSLg not running. `wsl --update` and reopen.
- **`AttributeError: numpy has no attribute 'ndarray'`** — you have numpy ≥ 2.0 conflicting with rclpy. `pip install 'numpy<2'` inside the env.
- **`unitree_sdk2py` import fails** — `requirements.txt` makes it optional. Lessons 01–06 don't need it; lessons 07–09 do.
- **`.discovered.sh` mentions a stale env** — `rm install/.discovered.sh` and re-run `bash install/install.sh`.
