#!/usr/bin/env bash
# deploy_and_test.sh — single command for "give me a ready-to-demo system."
#
# Runs the full install → build → test pipeline, then opens the
# walkthrough HTML if a browser is available. Prints next-step
# commands at the end.
#
# Usage:
#   bash scripts/deploy_and_test.sh                 # full: install + fetch G1 URDF (~150 MB) + build + e2e
#   bash scripts/deploy_and_test.sh --no-g1         # skip the G1 asset fetch (useful offline / in CI)

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

skip_g1=0
for arg in "$@"; do
  case "$arg" in
    -h|--help) sed -n '2,15p' "$0"; exit 0 ;;
    --no-g1|--skip-fetch) skip_g1=1 ;;
    *) fail "unknown arg: $arg"; exit 2 ;;
  esac
done

log "step 1/4 — install discovery + pip extras"
# Tee the full log so the user sees actionable failures from
# install/02_robostack_ros2.sh (e.g. "set TUTORIAL_INSTALL_ROS=1").
inst_log=$(mktemp -t deploy_install.XXXXXX.log)
if bash install/install.sh 2>&1 | tee "$inst_log" | tail -5; then
  :
else
  fail "install.sh failed — full log: $inst_log"
  exit 1
fi

g1_present_check="ws/src/g1_description/g1_29dof.urdf"
if (( skip_g1 )); then
  log "step 2a/4 — --no-g1 passed; skipping Unitree G1 asset fetch"
elif [[ ! -f "$g1_present_check" ]]; then
  log "step 2a/4 — fetching Unitree G1 URDF + meshes (~150 MB) from upstream GitHub"
  if ! bash install/06_fetch_g1_assets.sh; then
    warn "G1 asset fetch failed (offline? rate-limited?); continuing without G1 sim."
    warn "  re-run later with: bash install/06_fetch_g1_assets.sh"
  fi
else
  log "step 2a/4 — G1 assets already present, skipping fetch"
fi

log "step 2/4 — colcon build"
bash scripts/ros2_build.sh 2>&1 | tail -3

log "step 3/4 — full e2e test"
e2e_args=()
(( skip_g1 )) && e2e_args+=("--skip-fetch")
if bash tests/integration/full_e2e.sh "${e2e_args[@]}"; then
  log "step 4/4 — all tests green"
else
  fail "e2e failed — see /tmp/e2e_*.log"
  exit 1
fi

# Open the walkthrough in the host's default browser, cross-OS.
URL="file://$REPO_ROOT/docs/walkthrough.html"
# shellcheck source=../install/_os.sh
source "$REPO_ROOT/install/_os.sh"
if tutorial_open_url "$URL" 2>/dev/null; then
  log "opened walkthrough: $URL"
else
  log "open the walkthrough manually: $URL"
fi

cat <<EOF

${GREEN}═══════════════════════════════════════════════${NC}
  Ready to demo. Next:

  1) Activate the env in any new shell:
       source scripts/ros2_env.sh

  2) Bring up the Unitree G1 in rviz2:
       bash scripts/tools/sim_up.sh              # default: wave
       bash scripts/tools/sim_up.sh walk         # walking gait
       bash scripts/tools/sim_up.sh squat        # squat cycle
       bash scripts/tools/sim_up.sh tpose        # T-pose
       bash scripts/tools/sim_up.sh stretch      # full-body rotation

  3) Open the walkthrough:
       $URL
${GREEN}═══════════════════════════════════════════════${NC}

EOF
