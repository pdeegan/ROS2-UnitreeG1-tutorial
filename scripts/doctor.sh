#!/usr/bin/env bash
# doctor.sh — diagnostic dump. Safe to share when filing bug reports.
set -uo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

OUT="$REPO_ROOT/doctor_report_$(date +%Y%m%d_%H%M%S).txt"
exec > >(tee "$OUT") 2>&1

section() { printf "\n────── %s ──────\n" "$*"; }

section "host"
uname -a
[[ -f /etc/os-release ]] && cat /etc/os-release
grep -i microsoft /proc/version 2>/dev/null && echo "WSL2 detected"

section "disk"
df -h "$REPO_ROOT" | head -3

section "discovered paths"
if [[ -f install/.discovered.sh ]]; then
  cat install/.discovered.sh
else
  echo "install/.discovered.sh missing — run install/install.sh"
fi

# shellcheck source=/dev/null
[[ -f install/.discovered.sh ]] && source install/.discovered.sh || true
MAMBA_BIN="${TUTORIAL_MAMBA_BIN:-}"
ENV_DIR="${TUTORIAL_ROS_ENV:-}"

section "micromamba"
[[ -x "$MAMBA_BIN" ]] && "$MAMBA_BIN" --version || echo "not found"

section "ros2 env"
if [[ -n "$ENV_DIR" && -d "$ENV_DIR" ]]; then
  "$MAMBA_BIN" run -p "$ENV_DIR" python --version
  "$MAMBA_BIN" run -p "$ENV_DIR" ros2 --help 2>&1 | head -3
  "$MAMBA_BIN" run -p "$ENV_DIR" python -c "
import sys, importlib.metadata as m
mods = ['rclpy','cyclonedds','unitree_sdk2py','numpy','sounddevice','soundfile','onnxruntime','piper','pytest']
for mod in mods:
    try:
        __import__(mod)
        try: ver = m.version(mod.replace('_','-'))
        except Exception: ver = '?'
        print(f'  {mod:20s} OK   v{ver}')
    except Exception as e:
        print(f'  {mod:20s} MISS {e.__class__.__name__}: {e}')
"
else
  echo "ENV_DIR unset or missing"
fi

section "ros2 daemon + topics"
if [[ -n "$ENV_DIR" ]]; then
  export MAMBA_ROOT_PREFIX="${TUTORIAL_MAMBA_ROOT:-}"
  "$MAMBA_BIN" run -p "$ENV_DIR" ros2 daemon status 2>&1 | head -3
  "$MAMBA_BIN" run -p "$ENV_DIR" ros2 topic list 2>&1 | head -10 || true
fi

section "network interfaces"
ip -br addr 2>/dev/null || ifconfig -a 2>/dev/null | head -30

section "GPU"
if command -v nvidia-smi &>/dev/null; then
  nvidia-smi 2>&1 | head -15
else
  echo "no nvidia-smi"
fi
[[ -e /dev/dxg ]] && echo "/dev/dxg present" || echo "/dev/dxg missing"

section "workspace state"
if [[ -d ws/install ]]; then
  echo "ws/install exists. installed packages:"
  ls ws/install | head
else
  echo "ws/install missing — workspace not built"
fi

section "CycloneDDS env"
echo "CYCLONEDDS_URI=${CYCLONEDDS_URI:-<unset>}"
echo "RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION:-<unset>}"
echo "ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-<unset>}"

section "summary"
echo "report saved to: $OUT"
