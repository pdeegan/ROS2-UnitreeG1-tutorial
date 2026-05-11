# CLAUDE.md — ROS 2 Humanoid Tutorial

Project-level engineering guidelines for this tutorial repo. Loaded
automatically by Claude Code, Codex CLI (via `AGENTS.md` symlink),
Cursor, and any agent that follows the AGENTS.md convention.

This file overrides the parent user-level `~/.claude/CLAUDE.md` for
project-specific rules. Read it before non-trivial changes.

---

## What this project is

A **hands-on ROS 2 (Jazzy or Humble) tutorial** for humanoid
robotics, target hardware **Unitree G1**, target host **Debian 13
(trixie) WSL2 + NVIDIA discrete GPU**. Reference environment for
the tutorial body is Jazzy via the developer's existing
`~/micromamba/envs/ros2_jazzy` env.

It is pedagogical infrastructure: each lesson is a complete colcon
package readers can build, run, modify, and break. The G1 packages
are minimal scaffolds — not a production stack — that demonstrate the
*shape* of a humanoid bridge.

Read these in order before any non-trivial change:

1. [README.md](README.md) — repo map, quick start
2. [docs/architecture.md](docs/architecture.md) — system topology
3. [install/INSTALL.md](install/INSTALL.md) — install model & invariants
4. [docs/unitree_g1.md](docs/unitree_g1.md) — G1 connection + safety

---

## Architectural commitments (do not regress)

These are contracts. Weakening any of them must be rejected, or
accompanied by an explicit amendment to this file and to the affected
docs.

1. **One install path.** RoboStack (conda-forge) for ROS 2 (Jazzy or
   Humble) + pip layer for Unitree/audio/ML extras. No apt-based ROS
   install, no Docker entry point — Debian trixie has no upstream
   ROS apt repo, so we don't pretend.
2. **Discovery-first install.** Probe for existing micromamba + ROS
   env first, only download what's missing. Creating a fresh env
   requires explicit `TUTORIAL_INSTALL_ROS=1` opt-in (it's ~3.5 GB).
3. **Idempotent install scripts.** `install/*.sh` must be safe to
   re-run. Detect and skip; never blindly clobber.
4. **No motion without consent.** Every G1 motion command path checks
   `/g1/safety_engaged` before publishing `lowcmd`. The check is
   structural, not a comment.
5. **Lessons are self-contained packages.** Each `ws/src/tutorial_*`
   builds in isolation: a reader can `colcon build --packages-select
   tutorial_pubsub` and run it without touching the others.
6. **Lessons climb monotonically.** Lesson N may depend on N-1's
   concepts but not on its code. Each lesson is its own package.
7. **Python 3.11+ floor, 3.12 reference.** RoboStack Jazzy on trixie
   ships 3.12; Humble ships 3.11. Avoid 3.13-only syntax. The lessons
   use only stdlib features available in both.
8. **No silent network calls in install.** Every download in
   `install/` prints a line before fetching, so the user knows what's
   happening on a slow link.
9. **The HTML walkthrough is one self-contained file.** No CDN, no
   external fonts, no external CSS. Open offline, render correctly.
10. **Tests run without a robot.** Smoke tests must pass with no G1
    present. Tests requiring hardware are marked
    `@pytest.mark.hardware` and skipped by default.
11. **Use `scripts/ros2_build.sh`, not bare `colcon build`.** The env
    needs explicit Python + NumPy hints for `humanoid_msgs` to build
    on CMake 4.2; the helper script bakes them in.
12. **No `Co-Authored-By` trailers on commits.** See user CLAUDE.md.

---

## Build, verify

| Goal | Command |
|---|---|
| Full install (idempotent) | `bash install/install.sh` |
| Verify install | `bash install/05_verify.sh` |
| Activate env in current shell | `source scripts/ros2_env.sh` |
| Build all packages | `bash scripts/ros2_build.sh` |
| Build one package | `bash scripts/ros2_build.sh <name>` |
| Run smoke tests | `pytest tests/ -v` |
| Diagnostic dump | `bash scripts/doctor.sh` |
| Run a lesson | `bash scripts/run_tutorial.sh <NN>` |
| Bring up Unitree G1 in rviz2 | `bash scripts/tools/sim_up.sh` (or `walk`/`squat`/`tpose`/`stretch`) |
| Fetch G1 URDF assets | `bash install/06_fetch_g1_assets.sh` |
| Live system snapshot | `bash scripts/tools/inspect.sh` |
| Record / replay a bag | `bash scripts/tools/bag_record.sh` / `bag_play.sh` |

---

## When to spawn which specialist subagent

The `.claude/agents/` directory defines the specialist roster.
Auto-invoke by matching task; explicit invoke with
`Agent(subagent_type=...)`.

| Specialist | Use when |
|---|---|
| `ros2-architect` | Designing a new lesson or restructuring topics |
| `ros-node-author` | Writing or editing an `rclpy` node |
| `colcon-builder` | Build failures, package.xml / setup.py / CMakeLists |
| `wsl-setup-checker` | WSL/NVIDIA/CycloneDDS env diagnosis |
| `unitree-integrator` | Anything touching the G1 SDK ↔ ROS 2 boundary |
| `tutorial-writer` | Lesson copy in `docs/walkthrough.html` and `docs/*.md` |

Spawn multiple in parallel for cross-cutting changes. The
`/ros-review` slash command bundles a parallel review of the current
diff.

---

## How to add things (canonical procedures)

### Add a new lesson
1. Decide what concept it teaches and what failure mode it prevents
   (a lesson with no failure mode is just a code dump).
2. `bash scripts/lesson_new.sh tutorial_<short_name>` (or run
   `/lesson-new` in Claude Code).
3. Implement under `ws/src/tutorial_<short_name>/` as an `ament_python`
   package with one entry point.
4. Add a section to `docs/walkthrough.html` linking to the package.
5. Add a smoke test to `tests/test_lessons.py`.
6. Update the lesson table in `README.md`.

### Edit a G1 bridge package
1. Hand off to `unitree-integrator`.
2. Run `pytest tests/test_imports.py` — the package must still import
   without a robot.
3. Run `bash scripts/doctor.sh` — env wiring must still report green.
4. Note any new SDK version pin in `install/04_unitree_sdk.sh`.

### Change the install path
1. Update both `install/install.sh` and `install/INSTALL.md`.
2. Update commitment #1 in this file if the path actually changed.
3. Walk a fresh shell through `install.sh` end-to-end.

---

## Tone and standards

- Plain language, operational over aspirational.
- Default to no comments. Only add one when the *why* is non-obvious.
  Identifiers carry the *what*.
- Confirm before destructive ops (`rm -rf`, force-push, `--no-verify`).
- Never add `Co-Authored-By` trailers on commits.
- Don't write planning, decision, or analysis docs unless asked. The
  walkthrough HTML is the canonical narrative.

---

## Safety: motion commands

When editing anything under `ws/src/g1_bridge/` or `g1_controller/`:

- The `safety_engaged` latch is **structural**, not a flag. If you
  refactor the publisher path, the latch must remain on the publish
  side, not the application side. A bug in `g1_controller` should
  still fail closed.
- Default torques and gains in lesson code must be conservative. A
  reader running `ros2 run g1_controller wave_client` for the first
  time should not see violent motion.
- Damping mode is the safe default state. Stand and walk modes are
  opt-in via explicit service calls.

---

## Cross-tool agent compatibility

This project supports Claude Code, Codex CLI, Cursor, and any agent
that follows the AGENTS.md convention. `AGENTS.md` is a symlink to
this file. Agent-specific config lives in `.claude/`. The instructions
in this file apply to **all** agents.

When in doubt: read this file, read [README.md](README.md), read the
relevant lesson package, then act.
