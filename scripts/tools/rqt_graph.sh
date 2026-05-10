#!/usr/bin/env bash
# rqt_graph.sh — open the live node/topic graph viewer.
#
# Run while other nodes are up. You'll see every node as a box and every
# topic as a line; the graph is the truth about who-talks-to-whom right now.
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

source scripts/ros2_env.sh
exec ros2 run rqt_graph rqt_graph
