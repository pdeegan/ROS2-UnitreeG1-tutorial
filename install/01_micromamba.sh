#!/usr/bin/env bash
# 01_micromamba.sh — locate an existing micromamba; only bootstrap if absent.
# Writes the discovered location to install/.discovered.sh for later steps.
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
log() { printf "[01_micromamba] %s\n" "$*"; }

CANDIDATES=(
  "$HOME/.local/bin/micromamba"
  "$HOME/micromamba/bin/micromamba"
  "$(command -v micromamba 2>/dev/null || true)"
  "$REPO_ROOT/.micromamba/bin/micromamba"
)

MAMBA_BIN=""
for c in "${CANDIDATES[@]}"; do
  if [[ -n "$c" && -x "$c" ]]; then
    MAMBA_BIN="$c"
    break
  fi
done

if [[ -n "$MAMBA_BIN" ]]; then
  log "found micromamba: $MAMBA_BIN ($("$MAMBA_BIN" --version))"
else
  log "no micromamba found in standard locations — bootstrapping into repo"
  ARCH="$(uname -m)"
  KERNEL="$(uname -s)"
  case "$KERNEL:$ARCH" in
    Linux:x86_64)   PLATFORM="linux-64"      ;;
    Linux:aarch64)  PLATFORM="linux-aarch64" ;;
    Linux:ppc64le)  PLATFORM="linux-ppc64le" ;;
    Darwin:x86_64)  PLATFORM="osx-64"        ;;
    Darwin:arm64)   PLATFORM="osx-arm64"     ;;
    *)
      echo "[01_micromamba] unsupported platform: $KERNEL/$ARCH" >&2
      echo "[01_micromamba] supported: linux-{x86_64,aarch64,ppc64le}, macOS-{x86_64,arm64}" >&2
      exit 1 ;;
  esac
  MAMBA_BIN="$REPO_ROOT/.micromamba/bin/micromamba"
  mkdir -p "$(dirname "$MAMBA_BIN")"
  URL="https://micro.mamba.pm/api/micromamba/${PLATFORM}/latest"
  log "downloading micromamba ($PLATFORM): $URL"
  TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
  curl -fsSL "$URL" -o "$TMP/mm.tar.bz2"
  tar -xjf "$TMP/mm.tar.bz2" -C "$TMP" bin/micromamba
  mv "$TMP/bin/micromamba" "$MAMBA_BIN"
  chmod +x "$MAMBA_BIN"
  log "micromamba installed: $("$MAMBA_BIN" --version)"
fi

# Discover root prefix that owns this binary
case "$MAMBA_BIN" in
  "$HOME/.local/bin/micromamba")   MAMBA_ROOT="$HOME/micromamba" ;;
  "$HOME/micromamba/bin/micromamba") MAMBA_ROOT="$HOME/micromamba" ;;
  "$REPO_ROOT/.micromamba/bin/micromamba") MAMBA_ROOT="$REPO_ROOT/.micromamba" ;;
  *) MAMBA_ROOT="${MAMBA_ROOT_PREFIX:-$HOME/micromamba}" ;;
esac
log "mamba root prefix: $MAMBA_ROOT"

cat > "$SCRIPT_DIR/.discovered.sh" <<EOF
# auto-written by 01_micromamba.sh; consumed by later install steps.
export TUTORIAL_MAMBA_BIN="$MAMBA_BIN"
export TUTORIAL_MAMBA_ROOT="$MAMBA_ROOT"
EOF
log "wrote $SCRIPT_DIR/.discovered.sh"
