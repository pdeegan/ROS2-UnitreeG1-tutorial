#!/usr/bin/env bash
# inspect.sh — print everything you'd want to know about the live ROS 2 system.
#
# Use while other nodes are running. Mirrors what a roboticist types to
# answer "what's going on right now?"
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

source scripts/ros2_env.sh

section() { printf "\n── %s ──\n" "$*"; }

section "nodes"
ros2 node list

section "topics + types"
ros2 topic list -t | column -t -s ' '

section "services"
ros2 service list

section "actions"
ros2 action list

section "parameters per node"
for n in $(ros2 node list 2>/dev/null); do
  printf "  %s:\n" "$n"
  ros2 param list "$n" 2>/dev/null | sed 's/^/    /'
done

section "rates (one second sample, top 5 topics)"
for t in $(ros2 topic list 2>/dev/null | head -5); do
  printf "  %-30s " "$t"
  timeout 1.2 ros2 topic hz "$t" 2>&1 | grep -m1 'average rate' || echo "(silent)"
done
