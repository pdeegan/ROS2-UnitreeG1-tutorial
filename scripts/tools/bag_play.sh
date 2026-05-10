#!/usr/bin/env bash
# bag_play.sh — replay a previously recorded rosbag.
#
# Usage:
#   bash scripts/tools/bag_play.sh                          # newest bag, default loop
#   bash scripts/tools/bag_play.sh bags/my_session          # specific bag
#   bash scripts/tools/bag_play.sh bags/my_session --rate 2 # 2x speed
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

source scripts/ros2_env.sh

bag="${1:-}"
if [[ -z "$bag" ]]; then
  bag="$(ls -td bags/*/ 2>/dev/null | head -1 || true)"
  if [[ -z "$bag" ]]; then
    echo "[bag_play] no bags found under bags/; record one first with bag_record.sh" >&2
    exit 1
  fi
  echo "[bag_play] using newest bag: $bag"
  shift || true
else
  shift
fi

exec ros2 bag play "$bag" "$@"
