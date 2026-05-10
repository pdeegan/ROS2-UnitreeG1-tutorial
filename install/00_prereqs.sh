#!/usr/bin/env bash
# 00_prereqs.sh — APT prereqs + locale. Idempotent.
set -euo pipefail
log() { printf "[00_prereqs] %s\n" "$*"; }

REQUIRED=(
  curl ca-certificates bzip2 git build-essential cmake pkg-config
  python3 python3-venv python3-pip
  libgl1 libglib2.0-0 libxkbcommon0 libegl1
  locales
)

missing=()
for pkg in "${REQUIRED[@]}"; do
  if ! dpkg -s "$pkg" &>/dev/null; then missing+=("$pkg"); fi
done

if (( ${#missing[@]} == 0 )); then
  log "all apt prereqs already installed."
else
  log "installing apt prereqs: ${missing[*]}"
  if [[ $EUID -ne 0 ]]; then
    sudo apt-get update -qq
    sudo apt-get install -y --no-install-recommends "${missing[@]}"
  else
    apt-get update -qq
    apt-get install -y --no-install-recommends "${missing[@]}"
  fi
fi

# Locale: ROS 2 expects a UTF-8 locale.
if locale -a 2>/dev/null | grep -qi '^en_us\.utf-\?8$'; then
  log "en_US.UTF-8 already generated."
else
  log "generating en_US.UTF-8 locale"
  if [[ $EUID -ne 0 ]]; then
    sudo locale-gen en_US.UTF-8 >/dev/null
  else
    locale-gen en_US.UTF-8 >/dev/null
  fi
fi

# WSL detection — informational only.
if grep -qi microsoft /proc/version 2>/dev/null; then
  log "WSL2 detected — that's the supported path."
  if [[ ! -e /dev/dxg ]]; then
    log "note: /dev/dxg not present. NVIDIA WSL passthrough may be inactive."
    log "      install Windows-side NVIDIA driver (>=535) and 'wsl --update'."
  else
    log "/dev/dxg present — NVIDIA WSL passthrough looks active."
  fi
fi

log "done."
