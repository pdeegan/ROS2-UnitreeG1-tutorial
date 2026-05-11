# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `LICENSE` (MIT), `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`.
- `.github/` with issue templates, PR template, and a CI workflow that
  runs the install probe, builds the workspace, and runs the pytest
  smoke suite on every push and PR.
- `pre_bash_guard.sh` hook for Claude Code: blocks destructive
  patterns (force-push, `rm -rf /`, curl-pipe-sudo) before execution.
- New generic agents under `.claude/agents/`: code-reviewer,
  code-skeptic, security-reviewer, dependency-auditor,
  regression-test-writer, debugger, docs-writer, perf-auditor.
- New slash commands under `.claude/commands/`: swe-review,
  swe-security, swe-debug, swe-add-test, swe-deps, swe-skeptic,
  swe-swarm-review.
- `--no-g1` flag for `scripts/deploy_and_test.sh` so the pipeline
  works offline / in CI without the 150 MB G1 asset fetch.

### Changed

- `install/00_prereqs.sh` adds `libasound2`/`libportaudio2` (apt) and
  `alsa-lib`/`portaudio` (dnf) so the speech demo works on a minimal
  Linux install; also adds `libxkbcommon-x11-0` (apt) /
  `libxkbcommon-x11` (dnf) so rviz2's Qt loads cleanly.
- `install/02_robostack_ros2.sh` detects `ROS_DISTRO` from
  `conda-meta` JSON metadata instead of the broken
  `micromamba run bash -c 'echo $ROS_DISTRO'` (which always returned
  empty because activate.d isn't sourced).
- `scripts/tools/bag_record.sh` uses portable `${arr[${#arr[@]}-1]}`
  indexing so the script works on macOS bash 3.2.
- `ws/src/g1_controller/g1_controller/demo.py` replaces the private
  `_state_machine.current_state[1]` probe with a tracked `_active`
  bool set in `on_activate`/`on_deactivate`.
- `ws/src/g1_bridge/g1_bridge/bridge.py` logs at ERROR (and repeats
  every 10 s) when `humanoid_msgs` isn't built, so the degraded
  state is impossible to miss.
- `ws/src/g1_speech/g1_speech/speak.py` no longer blocks the service
  executor on `sd.wait()` during TTS playback.
- `docs/walkthrough.html` and other docs: every `ros2 service call …
  Trigger` now passes the required `'{}'` payload.

### Removed

- `install/.discovered.sh` from git history (was leaking the
  reference machine's hardcoded paths to every clone).

### Fixed

- `docs/testing.md` referenced a non-existent `sim.launch.py`;
  corrected to `g1_sim.launch.py` (the only launch file that exists).
- `docs/architecture.md` contract table attributed `/g1/set_mode` to
  `g1_bridge`; it's actually owned by `g1_controller`.
- `install/06_fetch_g1_assets.sh` printed an invalid
  `bash scripts/tools/sim_up.sh g1` next-step (silent fallback to
  the `zero` pose); now prints the default form.
- `tests/test_lessons.py` bumped time-budget asserts from 2.0/2.5s
  to 5.0s for slow-CI robustness.

## [0.1.0] — 2026-05-10

First public release.

### Added

- Nine ROS 2 lessons (`tutorial_basics` through `tutorial_actions`,
  `tutorial_lifecycle`, `tutorial_tf`, `tutorial_sim`) wrapped as
  standalone `ament_python` colcon packages.
- `humanoid_msgs` (custom msg/srv/action types).
- `g1_bridge` (Unitree DDS ↔ ROS 2 boundary + structural safety latch).
- `g1_speech` (Piper-backed TTS service).
- `g1_controller` (lifecycle node + `/g1/set_mode` service).
- Self-contained HTML walkthrough at `docs/walkthrough.html`.
- Discovery-first cross-OS install (`install/00_prereqs.sh` through
  `06_fetch_g1_assets.sh`).
- Headless end-to-end test suite (`tests/integration/full_e2e.sh`).
- Cross-tool agent harness (`.claude/`, with AGENTS.md symlinked).

[Unreleased]: https://github.com/pdeegan/ROS2-UnitreeG1-tutorial/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/pdeegan/ROS2-UnitreeG1-tutorial/releases/tag/v0.1.0
