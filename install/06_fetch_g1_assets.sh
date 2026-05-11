#!/usr/bin/env bash
# 06_fetch_g1_assets.sh — fetch the real Unitree G1 URDF + meshes from
# the upstream `unitreerobotics/unitree_ros` repo on GitHub.
#
# Idempotent. Sparse-clones only the G1 robot assets (the parent repo
# carries other quadrupeds + humanoids we don't need).
#
# Output: ws/src/g1_description/  (a colcon package wrapping the URDF)
#
# Run order:
#   bash install/01_micromamba.sh
#   bash install/02_robostack_ros2.sh
#   bash install/06_fetch_g1_assets.sh   # network — pulls ~150 MB
#   bash scripts/ros2_build.sh g1_description
#
# Mandatory for tutorial_sim — without these assets, sim_up.sh and the
# G1 launch file have nothing to render.
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
log()  { printf "[06_fetch_g1] %s\n" "$*"; }
warn() { printf "[06_fetch_g1] WARN: %s\n" "$*"; }

UPSTREAM="https://github.com/unitreerobotics/unitree_ros.git"
UPSTREAM_BRANCH="master"
DEST="$REPO_ROOT/ws/src/g1_description"

if [[ -f "$DEST/g1_29dof.urdf" || -f "$DEST/urdf/g1_29dof.urdf" ]]; then
  log "g1_description already present at $DEST — skipping clone"
  log "  (delete the directory and re-run to refresh)"
  exit 0
fi

if ! command -v git >/dev/null; then
  echo "[06_fetch_g1] git is required" >&2; exit 1
fi

log "fetching G1 URDF + meshes from $UPSTREAM (sparse, depth=1)"
log "  this is a ~150 MB download (mostly STL meshes)"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

cd "$TMP"
git clone --depth 1 --filter=blob:none --sparse --branch "$UPSTREAM_BRANCH" "$UPSTREAM" upstream
cd upstream
git sparse-checkout set robots/g1_description

if [[ ! -d robots/g1_description ]]; then
  echo "[06_fetch_g1] sparse-checkout did not produce robots/g1_description/" >&2
  echo "[06_fetch_g1] upstream layout may have changed. try cloning manually:" >&2
  echo "  git clone --depth 1 $UPSTREAM ~/scratch/unitree_ros" >&2
  echo "  cp -r ~/scratch/unitree_ros/robots/g1_description $DEST" >&2
  exit 1
fi

log "copying robots/g1_description → $DEST"
mkdir -p "$DEST"
cp -r robots/g1_description/. "$DEST/"

# Drop a colcon package descriptor so the workspace knows about it.
log "writing $DEST/package.xml"
cat > "$DEST/package.xml" <<'XML'
<?xml version="1.0"?>
<package format="3">
  <name>g1_description</name>
  <version>0.1.0</version>
  <description>Unitree G1 humanoid URDF + meshes, vendored from
    https://github.com/unitreerobotics/unitree_ros (master branch).
    This package only installs the assets; it is meant to be loaded by
    robot_state_publisher via tutorial_sim's launch files.</description>
  <maintainer email="tutorial@example.com">ROS Tutorial</maintainer>
  <license>BSD-3-Clause</license>

  <buildtool_depend>ament_cmake</buildtool_depend>

  <export>
    <build_type>ament_cmake</build_type>
  </export>
</package>
XML

cat > "$DEST/CMakeLists.txt" <<'CMAKE'
cmake_minimum_required(VERSION 3.14)
project(g1_description)

find_package(ament_cmake REQUIRED)

# Install everything under share/g1_description so robot_state_publisher
# and rviz can resolve `package://g1_description/...` URIs.
install(
  DIRECTORY .
  DESTINATION share/${PROJECT_NAME}
  PATTERN ".git" EXCLUDE
  PATTERN "CMakeLists.txt" EXCLUDE
  PATTERN "package.xml" EXCLUDE
)

ament_package()
CMAKE

# Quick sanity check
urdfs=$(find "$DEST" -maxdepth 2 -name '*.urdf' | wc -l)
meshes=$(find "$DEST" -name '*.STL' -o -name '*.stl' -o -name '*.dae' 2>/dev/null | wc -l)
log "vendored: $urdfs URDF variant(s), $meshes mesh file(s)"
log "next: bash scripts/ros2_build.sh g1_description"
log "      bash scripts/tools/sim_up.sh        # G1 is the default; or walk/squat/tpose/wave"
