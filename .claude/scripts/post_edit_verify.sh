#!/usr/bin/env bash
# post_edit_verify.sh — cheap syntax check on edited Python files.
# Reads $CLAUDE_TOOL_INPUT JSON via env var; falls back to a recent-edits scan.
set -uo pipefail
REPO="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# Try to grab the file Claude just touched from the hook env.
target="${CLAUDE_TOOL_INPUT_file_path:-}"

if [[ -z "$target" ]]; then
  # No way to extract — silently exit. Hook is best-effort.
  exit 0
fi

# Only check Python files inside the workspace or tests/.
case "$target" in
  *.py)
    if [[ "$target" == *"/ws/src/"* || "$target" == *"/tests/"* || "$target" == *"/scripts/"* ]]; then
      python3 -m py_compile "$target" 2>&1
      rc=$?
      if (( rc != 0 )); then
        echo "[post_edit_verify] syntax error in $target" >&2
        exit 2
      fi
    fi
    ;;
  *.sh)
    bash -n "$target" 2>&1
    rc=$?
    if (( rc != 0 )); then
      echo "[post_edit_verify] bash syntax error in $target" >&2
      exit 2
    fi
    ;;
esac
exit 0
