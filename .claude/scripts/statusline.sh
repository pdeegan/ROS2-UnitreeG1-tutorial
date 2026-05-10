#!/usr/bin/env bash
# statusline.sh — concise status. Reads stdin (JSON from Claude Code).
set -uo pipefail
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"

distro="-"
if [[ -f "$REPO/install/.discovered.sh" ]]; then
  # shellcheck source=/dev/null
  source "$REPO/install/.discovered.sh" 2>/dev/null || true
  distro="${TUTORIAL_ROS_DISTRO:-?}"
fi

if [[ -f "$REPO/ws/install/setup.bash" ]]; then
  ws="ws✓"
else
  ws="ws✗"
fi

dds="-"
[[ -n "${CYCLONEDDS_URI:-}" ]] && dds="dds✓"

branch=""
if [[ -d "$REPO/.git" ]]; then
  branch="$(git -C "$REPO" rev-parse --abbrev-ref HEAD 2>/dev/null || echo)"
fi

printf 'ROS-tutorial [%s] %s %s' "$distro" "$ws" "$dds"
[[ -n "$branch" ]] && printf ' (%s)' "$branch"
