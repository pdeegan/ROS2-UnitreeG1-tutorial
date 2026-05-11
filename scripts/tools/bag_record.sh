#!/usr/bin/env bash
# bag_record.sh — record specified topics (or all) to a rosbag.
#
# Usage:
#   bash scripts/tools/bag_record.sh                       # record EVERYTHING
#   bash scripts/tools/bag_record.sh /joint_states /tf     # specific topics
#   bash scripts/tools/bag_record.sh -o my_session /joint_states
#
# Output: a directory under bags/ that you can replay with bag_play.sh.
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"
mkdir -p bags

source scripts/ros2_env.sh

# If no topic args, record everything currently visible.
if [[ $# -eq 0 ]]; then
  echo "[bag_record] recording ALL topics — Ctrl+C to stop"
  cd bags
  exec ros2 bag record -a
fi

# Split args into flags (start with -) and positional topic names.
# rosbag2 deprecated positional topics; pass them via --topics.
flags=(); topics=()
need_outname=1
for a in "$@"; do
  case "$a" in
    -o|--output) need_outname=0; flags+=("$a") ;;
    -*)          flags+=("$a") ;;
    *)
      # Was the previous flag -o or --output? Then this is the output name.
      # macOS ships bash 3.2 which lacks ${arr[-1]} negative indexing; use
      # the explicit ${arr[${#arr[@]}-1]} form so the script works on both
      # Linux bash >=4 and macOS /bin/bash.
      _flags_last=""
      if (( ${#flags[@]} > 0 )); then
        _flags_last="${flags[${#flags[@]}-1]}"
      fi
      if [[ "$_flags_last" == "-o" || "$_flags_last" == "--output" ]]; then
        flags+=("$a")
      else
        topics+=("$a")
      fi
      ;;
  esac
done

# Default to a timestamped name if no -o was provided.
if (( need_outname )); then
  flags=( -o "session_$(date +%Y%m%d_%H%M%S)" "${flags[@]}" )
fi

cd bags
if (( ${#topics[@]} > 0 )); then
  exec ros2 bag record "${flags[@]}" --topics "${topics[@]}"
else
  exec ros2 bag record "${flags[@]}"
fi
