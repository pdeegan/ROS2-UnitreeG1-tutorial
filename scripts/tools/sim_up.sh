#!/usr/bin/env bash
# sim_up.sh — bring up a simulated humanoid in rviz2.
#
# Usage:
#   bash scripts/tools/sim_up.sh                # toy humanoid (no fetch needed)
#   bash scripts/tools/sim_up.sh g1             # real Unitree G1 (needs assets)
#   bash scripts/tools/sim_up.sh toy walk       # toy + walk gait
#   bash scripts/tools/sim_up.sh g1 walk false  # real G1, walk, headless
#
# Args:
#   $1  robot   = toy | g1            (default: toy)
#   $2  pattern = wave | walk | zero  (default: wave)
#   $3  rviz    = true | false        (default: true)
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

# shellcheck source=../ros2_env.sh
source scripts/ros2_env.sh

robot="${1:-toy}"
pattern="${2:-wave}"
rviz="${3:-true}"

# Kill any stale sim from a previous run. Without this you can end up
# with TWO robot_state_publishers broadcasting different URDFs to /tf,
# which makes rviz show a confused mash-up of toy + G1 frames.
echo "[sim_up] killing any stale sim processes…"
pkill -KILL -f 'tutorial_sim/lib/'        2>/dev/null || true
pkill -KILL -f 'joint_animator'           2>/dev/null || true
pkill -KILL -f '/lib/robot_state_publisher/' 2>/dev/null || true
pkill -KILL -f 'rviz2 .*humanoid.rviz'    2>/dev/null || true
pkill -KILL -f 'rviz2 .*g1.rviz'          2>/dev/null || true
sleep 0.5
ros2 daemon stop > /dev/null 2>&1 || true
sleep 0.3
ros2 daemon start > /dev/null 2>&1 || true

case "$robot" in
  toy)
    exec ros2 launch tutorial_sim sim.launch.py pattern:="$pattern" rviz:="$rviz"
    ;;
  g1|G1)
    g1_built_top="ws/install/g1_description/share/g1_description/g1_29dof.urdf"
    g1_built_sub="ws/install/g1_description/share/g1_description/urdf/g1_29dof.urdf"
    g1_src_top="ws/src/g1_description/g1_29dof.urdf"
    g1_src_sub="ws/src/g1_description/urdf/g1_29dof.urdf"
    if [[ ! -f "$g1_built_top" && ! -f "$g1_built_sub" \
       && ! -f "$g1_src_top"   && ! -f "$g1_src_sub" ]]; then
      cat >&2 <<EOF
[sim_up] G1 assets not found. Fetch + build them with:
    bash install/06_fetch_g1_assets.sh
    bash scripts/ros2_build.sh g1_description
EOF
      exit 1
    fi
    exec ros2 launch tutorial_sim g1_sim.launch.py pattern:="$pattern" rviz:="$rviz"
    ;;
  *)
    echo "[sim_up] unknown robot '$robot' — use 'toy' or 'g1'" >&2
    exit 1
    ;;
esac
