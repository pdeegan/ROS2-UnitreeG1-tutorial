#!/usr/bin/env bash
# 02_robostack_ros2.sh — locate an existing ROS 2 env (Jazzy or Humble).
# Only create a new one if none exists, and even then prompt first because
# a fresh env is ~3.5 GB of download.
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
log()  { printf "[02_robostack] %s\n" "$*"; }
warn() { printf "[02_robostack] WARN: %s\n" "$*"; }

# shellcheck source=/dev/null
[[ -f "$SCRIPT_DIR/.discovered.sh" ]] && source "$SCRIPT_DIR/.discovered.sh"
MAMBA_BIN="${TUTORIAL_MAMBA_BIN:-}"
MAMBA_ROOT="${TUTORIAL_MAMBA_ROOT:-}"
[[ -x "$MAMBA_BIN" ]] || { echo "micromamba not discovered — run 01_micromamba.sh" >&2; exit 1; }
export MAMBA_ROOT_PREFIX="$MAMBA_ROOT"

env_works() {
  local prefix="$1"
  [[ -x "$prefix/bin/ros2" ]] || return 1
  "$MAMBA_BIN" run -p "$prefix" python -c "import rclpy" &>/dev/null
}

# Candidate env paths to probe, in preference order.
CANDIDATES=(
  "$MAMBA_ROOT/envs/ros2_jazzy"
  "$MAMBA_ROOT/envs/ros2_humble"
  "$MAMBA_ROOT/envs/ros2"
  "$REPO_ROOT/.env_ros2"
)

ENV_DIR=""
ENV_DISTRO=""
for cand in "${CANDIDATES[@]}"; do
  if env_works "$cand"; then
    ENV_DIR="$cand"
    # Detect distro from package list
    if "$MAMBA_BIN" run -p "$cand" python -c "import rclpy, os; print(os.environ.get('ROS_DISTRO',''))" 2>/dev/null | grep -q .; then
      ENV_DISTRO="$("$MAMBA_BIN" run -p "$cand" bash -c 'echo $ROS_DISTRO' 2>/dev/null || echo unknown)"
    fi
    # Fallback: look at the env name
    if [[ -z "$ENV_DISTRO" ]]; then
      case "$cand" in
        *jazzy*)  ENV_DISTRO="jazzy"  ;;
        *humble*) ENV_DISTRO="humble" ;;
        *)        ENV_DISTRO="unknown" ;;
      esac
    fi
    break
  fi
done

if [[ -n "$ENV_DIR" ]]; then
  log "found working ROS 2 env: $ENV_DIR (distro: $ENV_DISTRO)"
  ros_version=$("$MAMBA_BIN" run -p "$ENV_DIR" ros2 --help 2>&1 | head -1 || true)
  log "ros2 CLI: $ros_version"
  python_ver=$("$MAMBA_BIN" run -p "$ENV_DIR" python --version 2>&1)
  log "python: $python_ver"
else
  warn "no working ROS 2 env found under $MAMBA_ROOT/envs/"
  if [[ "${TUTORIAL_INSTALL_ROS:-0}" != "1" ]]; then
    cat >&2 <<EOF

  No ROS 2 env was found. To create one (RoboStack Humble, ~3.5 GB
  download), re-run with:

      TUTORIAL_INSTALL_ROS=1 bash install/install.sh

  This is opt-in to protect limited disk space.

EOF
    exit 1
  fi

  log "TUTORIAL_INSTALL_ROS=1 set — creating a new env at $MAMBA_ROOT/envs/ros2_humble"
  ENV_DIR="$MAMBA_ROOT/envs/ros2_humble"
  ENV_DISTRO="humble"
  "$MAMBA_BIN" create -y -p "$ENV_DIR" \
    -c robostack-staging -c conda-forge \
    python=3.11 \
    ros-humble-desktop \
    ros-humble-rmw-cyclonedds-cpp \
    colcon-common-extensions \
    rosdep cmake pkg-config make ninja
fi

# Append discovery
{
  echo "export TUTORIAL_ROS_ENV=\"$ENV_DIR\""
  echo "export TUTORIAL_ROS_DISTRO=\"$ENV_DISTRO\""
} >> "$SCRIPT_DIR/.discovered.sh"
log "wrote ROS env discovery to $SCRIPT_DIR/.discovered.sh"
