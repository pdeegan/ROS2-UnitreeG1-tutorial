#!/usr/bin/env bash
# ros2_build.sh — colcon build with the per-env CMake hints baked in.
#
# Why this exists: RoboStack Jazzy's CMake 4.2 doesn't auto-detect
# the Development.Module / NumPy components in a conda-style Python
# install. We pass them explicitly so the build "just works".
#
# Usage:
#   bash scripts/ros2_build.sh                 # full workspace
#   bash scripts/ros2_build.sh humanoid_msgs   # one package
#   bash scripts/ros2_build.sh --packages-select g1_bridge g1_controller

set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT/ws"

# shellcheck source=ros2_env.sh
source "$SCRIPT_DIR/ros2_env.sh"

if [[ -z "${CONDA_PREFIX:-}" ]]; then
  echo "[ros2_build] CONDA_PREFIX unset — ros2_env.sh failed to activate" >&2
  exit 1
fi

PYBIN="$CONDA_PREFIX/bin/python"
PY_INC="$($PYBIN -c 'import sysconfig; print(sysconfig.get_path("include"))')"
PY_LIB_NAME="$($PYBIN -c 'import sysconfig; print("libpython" + sysconfig.get_config_var("LDVERSION") + ".so")')"
PY_LIB="$CONDA_PREFIX/lib/$PY_LIB_NAME"
NPY_INC="$($PYBIN -c 'import numpy; print(numpy.get_include())')"

CMAKE_ARGS=(
  -DPython3_EXECUTABLE="$PYBIN"
  -DPython3_INCLUDE_DIR="$PY_INC"
  -DPython3_LIBRARY="$PY_LIB"
  -DPython3_NumPy_INCLUDE_DIR="$NPY_INC"
)

# Convenience: a single positional arg becomes --packages-select.
PASSTHROUGH=()
if (( $# == 1 )) && [[ "$1" != --* ]]; then
  PASSTHROUGH=(--packages-select "$1")
elif (( $# > 0 )); then
  PASSTHROUGH=("$@")
fi

echo "[ros2_build] python    : $PYBIN"
echo "[ros2_build] py_include: $PY_INC"
echo "[ros2_build] py_library: $PY_LIB"
echo "[ros2_build] numpy_inc : $NPY_INC"
echo "[ros2_build] colcon args: ${PASSTHROUGH[*]:-<all packages>}"

exec colcon build "${PASSTHROUGH[@]}" --cmake-args "${CMAKE_ARGS[@]}"
