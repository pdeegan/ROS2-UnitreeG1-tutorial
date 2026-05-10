#!/usr/bin/env bash
# deploy_and_test.sh — single command for "give me a ready-to-demo system."
#
# Runs the full install → build → test pipeline, then opens the
# walkthrough HTML if a browser is available. Prints next-step
# commands at the end.
#
# Usage:
#   bash scripts/deploy_and_test.sh                 # default — toy URDF only
#   bash scripts/deploy_and_test.sh --with-g1       # also fetches + builds the real Unitree G1 URDF (~150 MB)

set -uo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

# Use $'...' so the escape sequences are real ESC bytes — that way they
# render as color in both `printf` AND in `cat <<EOF` heredocs below.
GREEN=$'\033[0;32m'; RED=$'\033[0;31m'; YELLOW=$'\033[1;33m'; NC=$'\033[0m'
log()  { printf "%s[deploy]%s %s\n" "$GREEN" "$NC" "$*"; }
warn() { printf "%s[deploy]%s %s\n" "$YELLOW" "$NC" "$*"; }
fail() { printf "%s[deploy]%s %s\n" "$RED" "$NC" "$*" >&2; }

WITH_G1=0
for arg in "$@"; do
  case "$arg" in
    --with-g1) WITH_G1=1 ;;
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
  esac
done

log "step 1/4 — install discovery + pip extras"
bash install/install.sh 2>&1 | tail -5

if (( WITH_G1 == 1 )); then
  log "step 2a/4 — fetching real Unitree G1 URDF (~150 MB) from upstream GitHub"
  bash install/06_fetch_g1_assets.sh 2>&1 | tail -5
fi

log "step 2/4 — colcon build"
bash scripts/ros2_build.sh 2>&1 | tail -3

log "step 3/4 — full e2e test"
e2e_args=( --skip-fetch )
(( WITH_G1 == 1 )) && e2e_args=( --fetch-g1 )
if bash tests/integration/full_e2e.sh "${e2e_args[@]}"; then
  log "step 4/4 — all tests green"
else
  fail "e2e failed — see /tmp/e2e_*.log"
  exit 1
fi

# Try to open the walkthrough in the system browser
URL="file://$REPO_ROOT/docs/walkthrough.html"
if command -v wslview >/dev/null 2>&1; then
  log "opening walkthrough in your Windows browser via wslview"
  wslview "$URL" 2>/dev/null || true
elif command -v xdg-open >/dev/null 2>&1; then
  log "opening walkthrough via xdg-open"
  xdg-open "$URL" >/dev/null 2>&1 || true
else
  log "open the walkthrough manually:"
  log "  $URL"
fi

cat <<EOF

${GREEN}═══════════════════════════════════════════════${NC}
  Ready to demo. Next:

  1) Activate the env in any new shell:
       source scripts/ros2_env.sh

  2) Bring up the toy humanoid in rviz2:
       bash scripts/tools/sim_up.sh

EOF
if (( WITH_G1 == 1 )); then
  cat <<EOF
  3) Bring up the REAL Unitree G1 in rviz2:
       bash scripts/tools/sim_up.sh g1

EOF
else
  cat <<EOF
  3) (Optional) fetch the real Unitree G1 URDF for a richer demo:
       bash install/06_fetch_g1_assets.sh
       bash scripts/ros2_build.sh g1_description
       bash scripts/tools/sim_up.sh g1

EOF
fi
cat <<EOF
  4) Open the walkthrough:
       $URL
${GREEN}═══════════════════════════════════════════════${NC}

EOF
