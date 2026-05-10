#!/usr/bin/env bash
# session_start.sh — one-line health banner so Claude picks up cold.
set -uo pipefail
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"

env_str="env=?"
ws_str="ws=?"
robot_str=""

if [[ -f "$REPO/install/.discovered.sh" ]]; then
  # shellcheck source=/dev/null
  source "$REPO/install/.discovered.sh" 2>/dev/null || true
  if [[ -n "${TUTORIAL_ROS_DISTRO:-}" ]]; then
    env_str="env=${TUTORIAL_ROS_DISTRO}"
  fi
fi

if [[ -f "$REPO/ws/install/setup.bash" ]]; then
  pkg_count=$(ls "$REPO/ws/install" 2>/dev/null | grep -cv '^setup\|^_local' || true)
  ws_str="ws=built(${pkg_count}pkg)"
else
  ws_str="ws=unbuilt"
fi

if [[ -n "${CYCLONEDDS_URI:-}" ]]; then
  robot_str="dds=set"
fi

printf '[ROS-tutorial] %s | %s | %s\n' "$env_str" "$ws_str" "${robot_str:-dds=unset}"
