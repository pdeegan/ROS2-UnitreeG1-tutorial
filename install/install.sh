#!/usr/bin/env bash
# install.sh — entry point. Discovery-first: detect what's installed,
# only add what's missing. Idempotent. Safe to re-run.
#
# Designed for a host that already has ROS 2 (Jazzy or Humble) via
# micromamba — typical of a developer machine that already runs the
# Master Control Agent stack. If no ROS env is found, we offer to
# create one (RoboStack Humble) but never silently install ~3.5 GB.

set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
log()  { printf "${GREEN}[install]${NC} %s\n" "$*"; }
warn() { printf "${YELLOW}[install]${NC} %s\n" "$*"; }
fail() { printf "${RED}[install]${NC} %s\n" "$*" >&2; exit 1; }

log "ROS 2 humanoid tutorial installer (discovery-first)"
log "repo root: $REPO_ROOT"

steps=(
  "00_prereqs.sh        : apt prereqs (skips if already present)"
  "01_micromamba.sh     : locate or bootstrap micromamba"
  "02_robostack_ros2.sh : locate (or, if missing, create) ROS 2 env"
  "03_pip_layer.sh      : add missing pip extras to the existing env"
  "04_unitree_sdk.sh    : verify unitree_sdk2py + CycloneDDS profile"
  "05_verify.sh         : green-light check"
)
for s in "${steps[@]}"; do printf "       %s\n" "$s"; done

for s in "${steps[@]}"; do
  script="${s%% *}"
  log "──── $script ────"
  bash "$SCRIPT_DIR/$script" || fail "$script failed — fix and re-run install.sh"
done

log "all steps green."
log "next: source scripts/ros2_env.sh"
log "then: ros2 run tutorial_basics hello   (after first colcon build)"
log "open: docs/walkthrough.html"
