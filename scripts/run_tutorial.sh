#!/usr/bin/env bash
# run_tutorial.sh — run a specific tutorial lesson by number or name.
#
# Usage:
#   bash scripts/run_tutorial.sh 01
#   bash scripts/run_tutorial.sh tutorial_pubsub
#
# Builds the package if needed, then runs its primary entry point.

set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# shellcheck source=ros2_env.sh
source "$SCRIPT_DIR/ros2_env.sh"

ARG="${1:-}"
if [[ -z "$ARG" ]]; then
  echo "usage: $0 <lesson-number-or-package>"
  echo
  echo "lessons:"
  for d in ws/src/tutorial_* ws/src/g1_*; do
    [[ -d "$d" ]] || continue
    echo "  $(basename "$d")"
  done
  exit 1
fi

# Map numeric arg → package name
case "$ARG" in
  01|1) PKG="tutorial_basics"     ; ENTRY="hello"  ;;
  02|2) PKG="tutorial_pubsub"     ; ENTRY="talker" ;;
  03|3) PKG="tutorial_services"   ; ENTRY="server" ;;
  04|4) PKG="tutorial_actions"    ; ENTRY="server" ;;
  05|5) PKG="tutorial_lifecycle"  ; ENTRY="lifecycle_talker" ;;
  06|6) PKG="tutorial_tf"         ; ENTRY="static_publisher" ;;
  07|7) PKG="g1_bridge"           ; ENTRY="bridge" ;;
  08|8) PKG="g1_speech"           ; ENTRY="speak"  ;;
  09|9) PKG="g1_controller"       ; ENTRY="demo"   ;;
  *)    PKG="$ARG"                ; ENTRY="" ;;
esac

[[ -d "ws/src/$PKG" ]] || { echo "no such package: ws/src/$PKG" >&2; exit 1; }

# Build the package if its install dir is missing or stale.
if [[ ! -d "ws/install/$PKG" ]]; then
  echo "[run_tutorial] building $PKG …"
  (cd ws && colcon build --packages-select "$PKG")
  source ws/install/setup.bash
fi

if [[ -z "$ENTRY" ]]; then
  echo "[run_tutorial] no default entry point for $PKG — pick one:"
  ros2 pkg executables "$PKG"
  exit 0
fi

echo "[run_tutorial] ros2 run $PKG $ENTRY"
exec ros2 run "$PKG" "$ENTRY"
