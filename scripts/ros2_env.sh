# scripts/ros2_env.sh — source this in every shell that needs ROS 2.
#
# Usage:
#   source scripts/ros2_env.sh
#
# Idempotent. Re-sourcing is safe.

# Resolve repo root regardless of cwd
_RT_THIS_FILE="${BASH_SOURCE[0]:-$0}"
_RT_SCRIPT_DIR="$(cd -- "$(dirname -- "$_RT_THIS_FILE")" &>/dev/null && pwd)"
ROS_TUTORIAL_ROOT="$(cd "$_RT_SCRIPT_DIR/.." && pwd)"
export ROS_TUTORIAL_ROOT

# Pull discovered paths
if [[ -f "$ROS_TUTORIAL_ROOT/install/.discovered.sh" ]]; then
  # shellcheck source=/dev/null
  source "$ROS_TUTORIAL_ROOT/install/.discovered.sh"
else
  echo "[ros2_env] install/.discovered.sh missing — run 'bash install/install.sh' first" >&2
  return 1 2>/dev/null || exit 1
fi

# Activate the discovered env. We don't use `micromamba activate` here
# because it requires shell init; instead we mimic activation manually.
export MAMBA_ROOT_PREFIX="$TUTORIAL_MAMBA_ROOT"
export CONDA_PREFIX="$TUTORIAL_ROS_ENV"

case ":$PATH:" in
  *":$TUTORIAL_ROS_ENV/bin:"*) ;;
  *) export PATH="$TUTORIAL_ROS_ENV/bin:$PATH" ;;
esac

# Source the ROS 2 setup if present (RoboStack env ships it).
# Relax nounset around these sources: ament/colcon setup scripts reference
# AMENT_TRACE_SETUP_FILES and similar without guarding them, which trips
# any caller running under `set -u`.
_rt_had_nounset=0
case "$-" in *u*) _rt_had_nounset=1; set +u ;; esac

if [[ -f "$TUTORIAL_ROS_ENV/setup.bash" ]]; then
  # shellcheck source=/dev/null
  source "$TUTORIAL_ROS_ENV/setup.bash"
fi

if [[ -f "$ROS_TUTORIAL_ROOT/ws/install/setup.bash" ]]; then
  # shellcheck source=/dev/null
  source "$ROS_TUTORIAL_ROOT/ws/install/setup.bash"
fi

(( _rt_had_nounset )) && set -u
unset _rt_had_nounset

# CycloneDDS profile — only set if not already set.
if [[ -z "${CYCLONEDDS_URI:-}" && -f "$ROS_TUTORIAL_ROOT/install/cyclonedds.xml" ]]; then
  export CYCLONEDDS_URI="file://$ROS_TUTORIAL_ROOT/install/cyclonedds.xml"
fi

# Use CycloneDDS as the RMW. RoboStack ships rmw_cyclonedds_cpp.
export RMW_IMPLEMENTATION="${RMW_IMPLEMENTATION:-rmw_cyclonedds_cpp}"

# ROS DOMAIN: keep the tutorial isolated from anything else on the network.
export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-42}"

echo "[ros2_env] ROS_DISTRO=$ROS_DISTRO  RMW=$RMW_IMPLEMENTATION  DOMAIN=$ROS_DOMAIN_ID"
echo "[ros2_env] env: $TUTORIAL_ROS_ENV"
echo "[ros2_env] ws : $ROS_TUTORIAL_ROOT/ws"
