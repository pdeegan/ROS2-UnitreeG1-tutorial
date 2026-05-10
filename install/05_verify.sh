#!/usr/bin/env bash
# 05_verify.sh — green-light check that the install is complete.
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { printf "${GREEN}✓${NC} %s\n" "$*"; }
warn() { printf "${YELLOW}!${NC} %s\n" "$*"; }
bad()  { printf "${RED}✗${NC} %s\n" "$*"; FAILED=1; }
FAILED=0

# shellcheck source=/dev/null
if [[ -f "$SCRIPT_DIR/.discovered.sh" ]]; then
  source "$SCRIPT_DIR/.discovered.sh"
else
  warn ".discovered.sh missing — running 01 and 02 first"
  bash "$SCRIPT_DIR/01_micromamba.sh" >/dev/null
  bash "$SCRIPT_DIR/02_robostack_ros2.sh" >/dev/null
  # shellcheck source=/dev/null
  source "$SCRIPT_DIR/.discovered.sh"
fi

MAMBA_BIN="${TUTORIAL_MAMBA_BIN:-}"
ENV_DIR="${TUTORIAL_ROS_ENV:-}"
DISTRO="${TUTORIAL_ROS_DISTRO:-unknown}"
export MAMBA_ROOT_PREFIX="${TUTORIAL_MAMBA_ROOT:-}"
RUN=( "$MAMBA_BIN" run -p "$ENV_DIR" )

[[ -x "$MAMBA_BIN" ]] && ok "micromamba: $MAMBA_BIN"        || bad "micromamba missing"
[[ -d "$ENV_DIR"   ]] && ok "ROS env: $ENV_DIR (distro: $DISTRO)" || bad "ROS env missing"

"${RUN[@]}" python -c "import rclpy"        &>/dev/null && ok "rclpy imports"        || bad "rclpy broken"
"${RUN[@]}" ros2 --help                     &>/dev/null && ok "ros2 CLI works"        || bad "ros2 CLI broken"
"${RUN[@]}" python -c "import cyclonedds"   &>/dev/null && ok "cyclonedds OK"         || warn "cyclonedds Python missing (g1_bridge needs it)"
"${RUN[@]}" python -c "import unitree_sdk2py" &>/dev/null && ok "unitree_sdk2py OK"   || warn "unitree_sdk2py missing (lessons 07-09 need it)"
"${RUN[@]}" python -c "import numpy"        &>/dev/null && ok "numpy OK"              || bad "numpy missing"
"${RUN[@]}" python -c "import sounddevice"  &>/dev/null && ok "sounddevice OK"        || warn "sounddevice missing (g1_speech needs it)"
"${RUN[@]}" python -c "import onnxruntime"  &>/dev/null && ok "onnxruntime OK"        || warn "onnxruntime missing (VAD lesson degraded)"
"${RUN[@]}" python -c "import piper"        &>/dev/null && ok "piper-tts OK"          || warn "piper-tts missing (TTS lesson degraded)"
"${RUN[@]}" python -c "import pytest"       &>/dev/null && ok "pytest OK"             || warn "pytest missing"
"${RUN[@]}" colcon --help                   &>/dev/null && ok "colcon OK"             || bad "colcon missing"

# nvidia smoke (informational)
if command -v nvidia-smi &>/dev/null && nvidia-smi -L &>/dev/null; then
  ok "GPU: $(nvidia-smi -L | head -1)"
else
  warn "no GPU detected (fine for lessons 01-06)"
fi
[[ -e /dev/dxg ]] && ok "/dev/dxg present (WSL NVIDIA passthrough active)" || warn "/dev/dxg missing (skip if not on WSL)"

if [[ -f "$REPO_ROOT/ws/install/setup.bash" ]]; then
  ok "workspace built (ws/install present)"
else
  warn "workspace not yet built — run: source scripts/ros2_env.sh && cd ws && colcon build"
fi

if (( FAILED == 0 )); then
  printf "\n${GREEN}install verified.${NC}  ROS distro: ${DISTRO}\n"
  echo "next: source scripts/ros2_env.sh"
  exit 0
else
  printf "\n${RED}install has failures above.${NC}\n" >&2
  exit 1
fi
