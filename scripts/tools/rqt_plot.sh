#!/usr/bin/env bash
# rqt_plot.sh — live numeric plotter for a topic field.
#
# Usage:
#   bash scripts/tools/rqt_plot.sh                       # opens empty; type a topic.field
#   bash scripts/tools/rqt_plot.sh /joint_states/position[0]
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

source scripts/ros2_env.sh
exec ros2 run rqt_plot rqt_plot "$@"
