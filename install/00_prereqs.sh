#!/usr/bin/env bash
# 00_prereqs.sh — system prereqs + locale. Idempotent. Cross-OS.
#
# Detects: Debian/Ubuntu (apt), Fedora/RHEL (dnf), macOS (brew),
# WSL2. Installs only what the OS supports, skips gracefully on
# minimal containers without sudo.
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
log() { printf "[00_prereqs] %s\n" "$*"; }

# shellcheck source=_os.sh
source "$SCRIPT_DIR/_os.sh"
log "detected OS: kind=$TUTORIAL_OS_KIND  family=$TUTORIAL_OS_FAMILY  pkg=$TUTORIAL_PKG  wsl=$TUTORIAL_IS_WSL"

# ─── packages by package manager ─────────────────────────────────────
case "$TUTORIAL_PKG" in
  apt)
    REQUIRED=(
      curl ca-certificates bzip2 xz-utils git build-essential cmake pkg-config
      python3 python3-venv python3-pip
      libgl1 libglib2.0-0 libxkbcommon0 libxkbcommon-x11-0 libegl1
      libasound2 libportaudio2
      locales
    )
    missing=()
    for pkg in "${REQUIRED[@]}"; do
      dpkg -s "$pkg" &>/dev/null || missing+=("$pkg")
    done
    if (( ${#missing[@]} == 0 )); then
      log "all apt prereqs already installed."
    else
      log "installing apt prereqs: ${missing[*]}"
      if [[ $EUID -ne 0 ]] && command -v sudo >/dev/null 2>&1; then
        sudo apt-get update -qq
        sudo apt-get install -y --no-install-recommends "${missing[@]}"
      elif [[ $EUID -eq 0 ]]; then
        apt-get update -qq
        apt-get install -y --no-install-recommends "${missing[@]}"
      else
        log "WARN: sudo not available; skipping apt install. Install these manually: ${missing[*]}"
      fi
    fi
    ;;

  dnf)
    REQUIRED=(curl ca-certificates bzip2 xz git gcc-c++ cmake pkgconfig
              python3 python3-pip mesa-libGL libxkbcommon libxkbcommon-x11
              alsa-lib portaudio glibc-langpack-en)
    missing=()
    for pkg in "${REQUIRED[@]}"; do
      rpm -q "$pkg" &>/dev/null || missing+=("$pkg")
    done
    if (( ${#missing[@]} == 0 )); then
      log "all dnf prereqs already installed."
    else
      log "installing dnf prereqs: ${missing[*]}"
      if [[ $EUID -ne 0 ]] && command -v sudo >/dev/null 2>&1; then
        sudo dnf install -y "${missing[@]}"
      elif [[ $EUID -eq 0 ]]; then
        dnf install -y "${missing[@]}"
      else
        log "WARN: sudo not available; skipping dnf install. Install manually: ${missing[*]}"
      fi
    fi
    ;;

  brew)
    log "macOS / Homebrew detected"
    # portaudio is needed by `sounddevice` for the speech-playback demo (g1_speech).
    REQUIRED=(curl bzip2 git cmake pkg-config python@3.12 portaudio)
    missing=()
    for pkg in "${REQUIRED[@]}"; do
      brew list "$pkg" &>/dev/null || missing+=("$pkg")
    done
    if (( ${#missing[@]} == 0 )); then
      log "all brew prereqs already installed."
    else
      log "installing brew prereqs: ${missing[*]}"
      brew install "${missing[@]}"
    fi
    ;;

  none)
    if [[ "$TUTORIAL_OS_FAMILY" == "macos" ]]; then
      log "WARN: Homebrew not installed. Install it from https://brew.sh and re-run."
      log "      Alternatively, ensure curl, bzip2, git, cmake, pkg-config, python3 are on PATH."
    else
      log "WARN: no recognized package manager. Skipping system prereqs."
      log "      Ensure curl, git, cmake, pkg-config, python3 are on PATH manually."
    fi
    ;;
esac

# ─── locale (Linux only — macOS ships UTF-8 by default) ──────────────
if [[ "$TUTORIAL_OS_FAMILY" == "linux" ]]; then
  if locale -a 2>/dev/null | grep -qiE '^en_us\.utf-?8$'; then
    log "en_US.UTF-8 already generated."
  elif command -v locale-gen >/dev/null 2>&1; then
    log "generating en_US.UTF-8 locale"
    if [[ $EUID -ne 0 ]] && command -v sudo >/dev/null 2>&1; then
      sudo locale-gen en_US.UTF-8 >/dev/null
    elif [[ $EUID -eq 0 ]]; then
      locale-gen en_US.UTF-8 >/dev/null
    else
      log "WARN: cannot generate locale without sudo; ROS 2 logging may misbehave."
    fi
  fi
fi

# ─── WSL-specific NVIDIA passthrough check ───────────────────────────
if (( TUTORIAL_IS_WSL == 1 )); then
  log "WSL2 detected"
  if [[ -e /dev/dxg ]]; then
    log "/dev/dxg present — NVIDIA WSL passthrough looks active."
  else
    log "note: /dev/dxg not present. NVIDIA WSL passthrough may be inactive."
    log "      Install Windows-side NVIDIA driver (>=535) and run 'wsl --update'."
  fi
fi

# ─── macOS-specific notes ────────────────────────────────────────────
if [[ "$TUTORIAL_OS_FAMILY" == "macos" ]]; then
  log "macOS notes:"
  log "  - rviz2 + GUI tools work natively via Qt (no XQuartz needed)."
  log "  - GPU acceleration uses Metal; CUDA/onnxruntime-gpu options don't apply."
  log "  - For real Unitree G1 wired connection, your Mac needs a NIC on the"
  log "    192.168.123.0/24 segment (USB-Ethernet adapter) and the cyclonedds_g1.xml"
  log "    interface name updated to match (run \`ifconfig\` to find it)."
fi

log "done."
