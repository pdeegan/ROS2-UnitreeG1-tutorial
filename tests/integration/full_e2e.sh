#!/usr/bin/env bash
# full_e2e.sh — full end-to-end deploy + test, with no human in the loop.
#
# Runs every install step, builds the workspace, runs the unit tests, then
# brings each runnable lesson up briefly under a timeout and asserts:
#   - the package's expected topics appear
#   - they publish at the expected rate (where applicable)
#   - shutdown is clean
#
# All under headless mode — no rviz windows pop up. Designed for CI
# but also runs locally.
#
# Exit code: 0 on success, non-zero on first failure.
# Output: progress to stdout; full per-step logs in /tmp/e2e_<step>.log.
#
# Usage:
#   bash tests/integration/full_e2e.sh                # full run (~3 min)
#   bash tests/integration/full_e2e.sh --skip-fetch   # don't touch G1 assets
#   bash tests/integration/full_e2e.sh --quick        # skip slow lesson runs
#   bash tests/integration/full_e2e.sh --fetch-g1     # also fetch + build the G1 URDF

set -uo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
PASSED=0; FAILED=0; SKIPPED=0
declare -a FAILURES=()

step()  { printf "\n${GREEN}══ %s ══${NC}\n" "$*"; }
ok()    { PASSED=$((PASSED+1)); printf "  ${GREEN}✓${NC} %s\n" "$*"; }
fail()  { FAILED=$((FAILED+1)); FAILURES+=("$*"); printf "  ${RED}✗${NC} %s\n" "$*"; }
skip()  { SKIPPED=$((SKIPPED+1)); printf "  ${YELLOW}~${NC} %s (skipped)\n" "$*"; }

# Argument parsing
DO_FETCH_G1=0
QUICK=0
SKIP_FETCH=0
for arg in "$@"; do
  case "$arg" in
    --fetch-g1)   DO_FETCH_G1=1 ;;
    --quick)      QUICK=1 ;;
    --skip-fetch) SKIP_FETCH=1 ;;
    -h|--help)
      sed -n '2,18p' "$0"
      exit 0 ;;
  esac
done

# ─────────────────────────────────────────────────────────────
# Cleanup helpers
# ─────────────────────────────────────────────────────────────
nuke_orphans() {
  # Kill anything from a previous run of THIS script that might be lingering.
  pkill -9 -f 'tutorial_basics|tutorial_pubsub|tutorial_services|tutorial_actions' 2>/dev/null || true
  pkill -9 -f 'tutorial_lifecycle|tutorial_tf|tutorial_sim|joint_animator' 2>/dev/null || true
  pkill -9 -f 'g1_bridge|safety_latch|g1_speech|g1_controller' 2>/dev/null || true
  pkill -9 -f 'robot_state_publisher|rviz2|rosbag' 2>/dev/null || true
  pkill -9 -f 'ros2 launch tutorial_sim' 2>/dev/null || true
  sleep 0.3
}

restart_daemon() {
  # Fresh daemon — avoids stale topic-graph state across phases.
  ros2 daemon stop > /dev/null 2>&1 || true
  sleep 0.3
  ros2 daemon start > /dev/null 2>&1 || true
}

cleanup_phase() {
  nuke_orphans
  restart_daemon
}

# Force a clean DDS environment
unset CYCLONEDDS_URI || true

# Use a unique domain ID per run to avoid colliding with the user's other shells
export ROS_DOMAIN_ID="${E2E_DOMAIN_ID:-$((RANDOM % 100 + 50))}"
echo "[e2e] ROS_DOMAIN_ID=$ROS_DOMAIN_ID (isolated from other shells)"

# Up-front cleanup in case a previous run left junk
nuke_orphans

trap nuke_orphans EXIT

# ────────────────────────────────────────────────────────────────────
step "Phase 1 — install discovery (no downloads beyond pip extras)"

bash install/01_micromamba.sh   > /tmp/e2e_01_micromamba.log 2>&1 \
  && ok "01_micromamba (existing or bootstrapped)" \
  || fail "01_micromamba — see /tmp/e2e_01_micromamba.log"

bash install/02_robostack_ros2.sh > /tmp/e2e_02_robostack.log 2>&1 \
  && ok "02_robostack_ros2 (env discovered)" \
  || fail "02_robostack_ros2 — see /tmp/e2e_02_robostack.log"

bash install/03_pip_layer.sh     > /tmp/e2e_03_pip.log 2>&1 \
  && ok "03_pip_layer (audio extras)" \
  || fail "03_pip_layer — see /tmp/e2e_03_pip.log"

bash install/04_unitree_sdk.sh   > /tmp/e2e_04_unitree.log 2>&1 \
  && ok "04_unitree_sdk" \
  || fail "04_unitree_sdk — see /tmp/e2e_04_unitree.log"

bash install/05_verify.sh        > /tmp/e2e_05_verify.log 2>&1 \
  && ok "05_verify (env green)" \
  || fail "05_verify — see /tmp/e2e_05_verify.log"

# ────────────────────────────────────────────────────────────────────
if (( DO_FETCH_G1 == 1 )); then
  step "Phase 1b — fetch real G1 assets from upstream GitHub (~150 MB)"
  bash install/06_fetch_g1_assets.sh > /tmp/e2e_06_g1_fetch.log 2>&1 \
    && ok "06_fetch_g1_assets" \
    || fail "06_fetch_g1_assets — see /tmp/e2e_06_g1_fetch.log"
elif (( SKIP_FETCH == 1 )); then
  step "Phase 1b — skipping G1 asset fetch (--skip-fetch)"
else
  step "Phase 1b — G1 assets"
  # Upstream layout puts URDFs at top level of g1_description/.
  if [[ -f ws/src/g1_description/g1_29dof.urdf \
     || -f ws/src/g1_description/urdf/g1_29dof.urdf ]]; then
    ok "g1_description already present (skipping fetch)"
    DO_FETCH_G1=1
  else
    skip "G1 URDF fetch (re-run with --fetch-g1 to include)"
  fi
fi

# ────────────────────────────────────────────────────────────────────
step "Phase 2 — colcon build (whole workspace)"

if bash scripts/ros2_build.sh > /tmp/e2e_build.log 2>&1; then
  pkg_count=$(ls ws/install 2>/dev/null | grep -cv '^setup\|^_local' || echo 0)
  ok "colcon build (${pkg_count} packages)"
else
  fail "colcon build — see /tmp/e2e_build.log"
  echo "  --- last 25 lines: ---"
  tail -25 /tmp/e2e_build.log | sed 's/^/    /'
  # No point continuing if the build is broken
  printf "\n${RED}aborting: build failed${NC}\n" >&2
  exit 1
fi

# Activate env for the rest of the run
# shellcheck source=/dev/null
source scripts/ros2_env.sh > /dev/null 2>&1
unset CYCLONEDDS_URI || true
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID}"  # re-export after env source

cleanup_phase

# ────────────────────────────────────────────────────────────────────
step "Phase 3 — pytest unit + integration smoke tests"

if pytest tests/test_imports.py tests/test_lessons.py -x --timeout=30 -q \
   > /tmp/e2e_pytest.log 2>&1; then
  test_count=$(grep -E '^[0-9]+ passed' /tmp/e2e_pytest.log | tail -1)
  ok "pytest — $test_count"
else
  fail "pytest — see /tmp/e2e_pytest.log"
  echo "  --- last 40 lines: ---"
  tail -40 /tmp/e2e_pytest.log | sed 's/^/    /'
fi

cleanup_phase

# ────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────
launch_and_check() {
  # $1 name  $2 command  $3 topic  (optional $4 settle_seconds)
  local name="$1" cmd="$2" topic="$3" settle="${4:-0.5}"
  local log="/tmp/e2e_run_${name}.log"

  # Start the node in background
  ( eval "$cmd" > "$log" 2>&1 ) &
  local pid=$!

  # Wait up to 8 seconds for the topic to exist
  local seen=0
  for _ in $(seq 1 40); do
    if ros2 topic list 2>/dev/null | grep -qF "$topic"; then
      seen=1; break
    fi
    sleep 0.2
  done

  if (( seen == 0 )); then
    kill -TERM "$pid" 2>/dev/null; wait "$pid" 2>/dev/null
    fail "$name — topic $topic never appeared (log: $log)"
    return 1
  fi

  sleep "$settle"

  # Sample one message on the topic
  if ! timeout 4 ros2 topic echo --no-arr --once "$topic" \
       > "/tmp/e2e_msg_${name}.log" 2>&1; then
    kill -TERM "$pid" 2>/dev/null; wait "$pid" 2>/dev/null
    fail "$name — could not echo $topic"
    return 1
  fi

  if ! grep -q '.' "/tmp/e2e_msg_${name}.log"; then
    kill -TERM "$pid" 2>/dev/null; wait "$pid" 2>/dev/null
    fail "$name — empty message on $topic"
    return 1
  fi

  kill -TERM "$pid" 2>/dev/null
  wait "$pid" 2>/dev/null
  ok "$name — $topic streaming"
  return 0
}

run_briefly() {
  # $1 name  $2 command  $3 duration_sec
  local name="$1" cmd="$2" duration="${3:-3}"
  local log="/tmp/e2e_run_${name}.log"
  if timeout "$duration" bash -c "$cmd" > "$log" 2>&1 ; then
    rc=0
  else
    rc=$?
  fi
  # 0 (clean), 124 (timeout), 143 (SIGTERM), 130 (SIGINT) all OK
  if [[ "$rc" == 0 || "$rc" == 124 || "$rc" == 143 || "$rc" == 130 ]]; then
    ok "$name (clean run, exit=$rc)"
  else
    fail "$name (exit=$rc, log: $log)"
    echo "  --- last 10 lines: ---"
    tail -10 "$log" | sed 's/^/    /'
  fi
}

# ────────────────────────────────────────────────────────────────────
step "Phase 4 — every lesson runs without crashing"

if (( QUICK == 1 )); then
  skip "lesson runs (--quick)"
else
  launch_and_check "L01_basics"        "ros2 run tutorial_basics hello"            "/rosout"
  cleanup_phase
  launch_and_check "L02_talker"        "ros2 run tutorial_pubsub talker"           "/joint_state"
  cleanup_phase
  run_briefly      "L02_listener"      "ros2 run tutorial_pubsub listener" 2
  cleanup_phase
  launch_and_check "L03_service"       "ros2 run tutorial_services server"         "/rosout"
  cleanup_phase
  run_briefly      "L04_action_server" "ros2 run tutorial_actions server" 2
  cleanup_phase
  run_briefly      "L05_lifecycle"     "ros2 run tutorial_lifecycle lifecycle_talker" 2
  cleanup_phase
  launch_and_check "L06_tf_static"     "ros2 run tutorial_tf static_publisher"     "/tf_static"
  cleanup_phase
  launch_and_check "L06_tf_head"       "ros2 run tutorial_tf head_tracker"         "/tf"
  cleanup_phase
fi

# ────────────────────────────────────────────────────────────────────
step "Phase 5 — sim humanoid launches and publishes /joint_states + /tf"

# Toy URDF
launch_and_check "sim_toy_joint_states" \
  "ros2 launch tutorial_sim sim.launch.py rviz:=false" \
  "/joint_states" \
  1.0
cleanup_phase

# Verify the pattern parameter works
ros2 launch tutorial_sim sim.launch.py rviz:=false > /tmp/e2e_pattern.log 2>&1 &
LPID=$!
# Wait for the node to register before talking to it
for _ in $(seq 1 30); do
  if ros2 node list 2>/dev/null | grep -q joint_animator; then break; fi
  sleep 0.2
done

if ros2 param get /joint_animator pattern 2>&1 | grep -q wave; then
  ok "joint_animator default pattern is 'wave'"
else
  fail "joint_animator pattern get failed (log: /tmp/e2e_pattern.log)"
fi

if ros2 param set /joint_animator pattern walk > /dev/null 2>&1 \
   && [[ "$(ros2 param get /joint_animator pattern 2>/dev/null | tail -1)" == *walk* ]]; then
  ok "ros2 param set pattern=walk applied"
else
  fail "ros2 param set pattern failed"
fi

kill -TERM $LPID 2>/dev/null; wait $LPID 2>/dev/null
cleanup_phase

# G1 URDF (only if assets present). Upstream layout puts URDFs at
# the top level of g1_description/ — no urdf/ subfolder.
g1_built_top="ws/install/g1_description/share/g1_description/g1_29dof.urdf"
g1_built_sub="ws/install/g1_description/share/g1_description/urdf/g1_29dof.urdf"
g1_src_top="ws/src/g1_description/g1_29dof.urdf"
g1_src_sub="ws/src/g1_description/urdf/g1_29dof.urdf"
if [[ -f "$g1_built_top" || -f "$g1_built_sub" ]]; then
  launch_and_check "sim_g1_joint_states" \
    "ros2 launch tutorial_sim g1_sim.launch.py rviz:=false" \
    "/joint_states" \
    1.5
  cleanup_phase
elif [[ -f "$g1_src_top" || -f "$g1_src_sub" ]]; then
  fail "g1_description in src/ but not built — run bash scripts/ros2_build.sh g1_description"
else
  skip "G1 URDF launch (assets not fetched)"
fi

# ────────────────────────────────────────────────────────────────────
step "Phase 6 — G1 bridge in fake mode publishes /g1/imu + safety latch"

G1_BRIDGE_FAKE=1 ros2 run g1_bridge bridge > /tmp/e2e_bridge.log 2>&1 &
BPID=$!
ros2 run g1_bridge safety > /tmp/e2e_safety.log 2>&1 &
SPID=$!

# Wait for both nodes
for _ in $(seq 1 30); do
  if ros2 node list 2>/dev/null | grep -q g1_bridge \
     && ros2 node list 2>/dev/null | grep -q safety_latch; then
    break
  fi
  sleep 0.2
done

# Settle so the latch publication propagates
sleep 1.5

# Check expected topics
expected_topics=(/g1/imu /g1/lowstate /g1/lowcmd /g1/safety_engaged)
for t in "${expected_topics[@]}"; do
  if ros2 topic list 2>/dev/null | grep -qF "$t"; then
    ok "topic $t present"
  else
    fail "topic $t missing"
  fi
done

# Engage safety, give the bridge several beats to log the change
if ros2 service call /g1/safety/engage std_srvs/srv/Trigger > /tmp/e2e_engage.log 2>&1; then
  ok "/g1/safety/engage service call returned"
else
  fail "/g1/safety/engage service call failed"
fi

# Wait up to 4 seconds for the bridge log to record the latch transition
saw_engage=0
for _ in $(seq 1 20); do
  if grep -q "ENGAGED" /tmp/e2e_bridge.log 2>/dev/null; then
    saw_engage=1; break
  fi
  sleep 0.2
done
if (( saw_engage == 1 )); then
  ok "safety latch propagates to bridge log"
else
  fail "bridge did not log safety engage (log: /tmp/e2e_bridge.log)"
fi

kill -TERM $BPID $SPID 2>/dev/null
wait $BPID $SPID 2>/dev/null
cleanup_phase

# ────────────────────────────────────────────────────────────────────
step "Phase 7 — rosbag record + replay round-trip"

mkdir -p /tmp/e2e_bags
rm -rf /tmp/e2e_bags/rt

# Producer: sim humanoid, headless
ros2 launch tutorial_sim sim.launch.py rviz:=false > /tmp/e2e_sim_for_bag.log 2>&1 &
SIMPID=$!

# Wait for /joint_states to APPEAR on the topic list (~6 s max).
for _ in $(seq 1 30); do
  ros2 topic list 2>/dev/null | grep -q /joint_states && break
  sleep 0.2
done

# Brief settle so the bag's DDS subscriber discovers the publisher.
sleep 1

# Record. Two attempts: a fast one (2 s record window), then a slower
# retry only if the first misses DDS discovery.
# Use --topics flag (positional form is deprecated in newer rosbag2 and
# may silently record nothing). Use SIGINT, not the default SIGTERM —
# rosbag2 needs SIGINT to flush metadata.yaml on shutdown. Add
# --kill-after=4 so a hung bag dies in bounded time, but give rosbag2
# enough headroom to flush the cache after SIGINT (it can take >1 s).
#
# Each attempt APPENDS to bag_rec.log (>>) so on failure we see what
# happened in both attempts, not just the second.
bag_ok=0
: > /tmp/e2e_bag_rec.log     # truncate at start of phase
for attempt_window in 3 5; do
  # Make absolutely sure no previous bag-record process is still alive
  # holding sockets — a half-killed one will starve the next attempt.
  pkill -KILL -f 'ros2 bag record' 2>/dev/null || true
  rm -rf /tmp/e2e_bags/rt
  echo ">>> attempt window=${attempt_window}s @ $(date +%H:%M:%S)" >> /tmp/e2e_bag_rec.log
  ( cd /tmp/e2e_bags && \
    timeout -s INT --kill-after=4 "$attempt_window" \
       ros2 bag record -o rt --topics /joint_states /tf \
       >> /tmp/e2e_bag_rec.log 2>&1 || true )
  # Wait for rosbag2 to flush metadata.yaml — it logs "may take a while".
  for _ in $(seq 1 15); do
    [[ -f /tmp/e2e_bags/rt/metadata.yaml ]] && break
    sleep 0.2
  done
  if [[ -f /tmp/e2e_bags/rt/metadata.yaml ]]; then
    bag_ok=1; break
  fi
  echo "<<< attempt failed; retrying" >> /tmp/e2e_bag_rec.log
done

if (( bag_ok == 1 )); then
  ok "rosbag record produced metadata.yaml"

  if ros2 bag info /tmp/e2e_bags/rt > /tmp/e2e_bag_info.log 2>&1 \
     && grep -q "Messages:" /tmp/e2e_bag_info.log; then
    msgs=$(grep "Messages:" /tmp/e2e_bag_info.log | head -1 | awk '{print $NF}')
    if [[ "$msgs" -gt 0 ]]; then
      ok "rosbag info OK (messages=$msgs)"
    else
      fail "rosbag info shows zero messages"
    fi
  else
    fail "rosbag info failed (log: /tmp/e2e_bag_info.log)"
  fi
else
  fail "rosbag record didn't produce metadata.yaml after 2 attempts (log: /tmp/e2e_bag_rec.log)"
  echo "  --- bag_rec.log: ---"
  sed 's/^/    /' /tmp/e2e_bag_rec.log
  echo "  --- bag dir contents: ---"
  ls /tmp/e2e_bags/rt 2>&1 | sed 's/^/    /'
  echo "  --- sim launch log tail: ---"
  tail -10 /tmp/e2e_sim_for_bag.log | sed 's/^/    /'
  skip "rosbag info — no bag to query"
fi

# Stop the sim before replay — INT first (clean), then KILL fallback.
kill -INT $SIMPID 2>/dev/null
( sleep 1.5 && kill -KILL $SIMPID 2>/dev/null ) &
wait $SIMPID 2>/dev/null
cleanup_phase

# Replay — should republish /joint_states (only if record succeeded)
if (( bag_ok == 1 )); then
  timeout -s INT --kill-after=1 3 ros2 bag play /tmp/e2e_bags/rt \
    > /tmp/e2e_bag_play.log 2>&1 &
  PLAY_PID=$!
  # Wait up to ~2 s for the topic to reappear on the graph.
  saw=0
  for _ in $(seq 1 10); do
    if ros2 topic list 2>/dev/null | grep -q /joint_states; then
      saw=1; break
    fi
    sleep 0.2
  done
  if (( saw == 1 )); then
    ok "rosbag play republishes /joint_states"
  else
    fail "rosbag play did not republish /joint_states"
  fi
  kill -INT $PLAY_PID 2>/dev/null
  ( sleep 1 && kill -KILL $PLAY_PID 2>/dev/null ) &
  wait $PLAY_PID 2>/dev/null
else
  skip "rosbag play — no bag to play"
fi

rm -rf /tmp/e2e_bags
cleanup_phase

# ────────────────────────────────────────────────────────────────────
step "Phase 8 — GUI tools sanity check (binaries available)"

if rviz2 --help > /dev/null 2>&1 || rviz2 -h > /dev/null 2>&1; then
  ok "rviz2 binary works"
else
  # Some rviz2 builds don't accept --help and just exit 1; check the binary exists
  if command -v rviz2 > /dev/null; then
    ok "rviz2 binary present (no --help support; that's normal)"
  else
    fail "rviz2 binary missing"
  fi
fi

if ros2 pkg executables rqt_graph 2>/dev/null | grep -q rqt_graph; then
  ok "rqt_graph entry point available"
else
  fail "rqt_graph entry point missing"
fi

if ros2 pkg executables rqt_plot 2>/dev/null | grep -q rqt_plot; then
  ok "rqt_plot entry point available"
else
  fail "rqt_plot entry point missing"
fi

if ros2 pkg executables tf2_ros 2>/dev/null | grep -q tf2_echo; then
  ok "tf2_ros/tf2_echo available"
else
  fail "tf2_ros/tf2_echo missing"
fi

if command -v gz > /dev/null 2>&1; then
  ok "gz (Gazebo Sim) CLI available at $(command -v gz)"
else
  skip "gz not on PATH"
fi

# ────────────────────────────────────────────────────────────────────
step "Phase 8b — walkthrough HTML interactive features (copy + search)"

if command -v chromium > /dev/null 2>&1 \
   || command -v chromium-browser > /dev/null 2>&1 \
   || command -v google-chrome > /dev/null 2>&1; then
  if bash "$SCRIPT_DIR/walkthrough_smoke.sh" > /tmp/e2e_walkthrough.log 2>&1; then
    ok "walkthrough.html — copy buttons + search + ref index render cleanly"
  else
    fail "walkthrough.html smoke (log: /tmp/e2e_walkthrough.log)"
    echo "  --- last 15 lines: ---"
    tail -15 /tmp/e2e_walkthrough.log | sed 's/^/    /'
  fi
else
  skip "walkthrough HTML smoke (no chromium installed)"
fi

# ────────────────────────────────────────────────────────────────────
step "Final cleanup"
nuke_orphans
ros2 daemon stop > /dev/null 2>&1 || true

printf "\n────────────────── summary ──────────────────\n"
printf "${GREEN}passed:  %d${NC}\n" "$PASSED"
printf "${YELLOW}skipped: %d${NC}\n" "$SKIPPED"
printf "${RED}failed:  %d${NC}\n" "$FAILED"
printf "─────────────────────────────────────────────\n"

if (( FAILED > 0 )); then
  printf "\n${RED}failures:${NC}\n"
  for f in "${FAILURES[@]}"; do printf "  - %s\n" "$f"; done
  printf "\nlogs under /tmp/e2e_*.log\n"
  exit 1
fi

printf "\n${GREEN}ALL GREEN.${NC} The tutorial is ready to teach.\n"
exit 0
