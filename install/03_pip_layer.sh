#!/usr/bin/env bash
# 03_pip_layer.sh — install ONLY the missing pip extras into the existing
# ROS 2 env. Probes each module before installing; skips what's present.
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
log() { printf "[03_pip_layer] %s\n" "$*"; }

# shellcheck source=/dev/null
source "$SCRIPT_DIR/.discovered.sh"
MAMBA_BIN="$TUTORIAL_MAMBA_BIN"
ENV_DIR="$TUTORIAL_ROS_ENV"
export MAMBA_ROOT_PREFIX="$TUTORIAL_MAMBA_ROOT"

# (module_name, pip_spec) pairs. Module is what `python -c "import X"` uses;
# pip_spec is what goes to pip if missing.
declare -a EXTRAS=(
  "sounddevice|sounddevice>=0.4.6"
  "soundfile|soundfile>=0.12"
  "onnxruntime|onnxruntime>=1.17"
  "piper|piper-tts>=1.2"
  "pytest_timeout|pytest-timeout>=2.2"
  "pytest_asyncio|pytest-asyncio>=0.23"
)

to_install=()
for spec in "${EXTRAS[@]}"; do
  mod="${spec%%|*}"
  pip_spec="${spec##*|}"
  if "$MAMBA_BIN" run -p "$ENV_DIR" python -c "import ${mod}" &>/dev/null; then
    log "skip ${mod} (already present)"
  else
    to_install+=("$pip_spec")
  fi
done

if (( ${#to_install[@]} == 0 )); then
  log "all pip extras already installed — nothing to do."
  exit 0
fi

log "installing pip extras: ${to_install[*]}"
"$MAMBA_BIN" run -p "$ENV_DIR" python -m pip install --no-input "${to_install[@]}"

log "verifying installs"
for spec in "${EXTRAS[@]}"; do
  mod="${spec%%|*}"
  if "$MAMBA_BIN" run -p "$ENV_DIR" python -c "import ${mod}" &>/dev/null; then
    log "  OK   ${mod}"
  else
    log "  WARN ${mod} still not importable (may have a system-level dep — check INSTALL.md)"
  fi
done
