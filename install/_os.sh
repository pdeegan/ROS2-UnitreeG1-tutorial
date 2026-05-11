#!/usr/bin/env bash
# _os.sh — sourced by other install scripts. Sets these read-only vars:
#
#   TUTORIAL_OS_KIND   one of: debian | ubuntu | redhat | macos | unknown
#   TUTORIAL_OS_FAMILY one of: linux | macos
#   TUTORIAL_IS_WSL    1 if running under WSL2, else 0
#   TUTORIAL_PKG       one of: apt | dnf | brew | none
#
# Don't run directly — `source` it.

# shellcheck disable=SC2034

TUTORIAL_OS_KIND="unknown"
TUTORIAL_OS_FAMILY="unknown"
TUTORIAL_IS_WSL=0
TUTORIAL_PKG="none"

case "$(uname -s)" in
  Linux)
    TUTORIAL_OS_FAMILY="linux"
    if grep -qi microsoft /proc/version 2>/dev/null; then
      TUTORIAL_IS_WSL=1
    fi
    if [[ -f /etc/os-release ]]; then
      # shellcheck source=/dev/null
      . /etc/os-release
      case "${ID:-}:${ID_LIKE:-}" in
        debian:*|*debian*|*:*debian*) TUTORIAL_OS_KIND="debian" ;;
        ubuntu:*|*ubuntu*|*:*ubuntu*) TUTORIAL_OS_KIND="ubuntu" ;;
        rhel:*|fedora:*|*rhel*|*:*rhel*|*:*fedora*) TUTORIAL_OS_KIND="redhat" ;;
      esac
      # ID alone for distros that don't set ID_LIKE
      [[ "$TUTORIAL_OS_KIND" == "unknown" ]] && case "${ID:-}" in
        debian) TUTORIAL_OS_KIND="debian" ;;
        ubuntu|pop|linuxmint) TUTORIAL_OS_KIND="ubuntu" ;;
        fedora|rhel|rocky|almalinux|centos) TUTORIAL_OS_KIND="redhat" ;;
      esac
    fi
    if   command -v apt-get >/dev/null 2>&1; then TUTORIAL_PKG="apt"
    elif command -v dnf     >/dev/null 2>&1; then TUTORIAL_PKG="dnf"
    fi
    ;;
  Darwin)
    TUTORIAL_OS_FAMILY="macos"
    TUTORIAL_OS_KIND="macos"
    if command -v brew >/dev/null 2>&1; then TUTORIAL_PKG="brew"; fi
    ;;
esac

export TUTORIAL_OS_KIND TUTORIAL_OS_FAMILY TUTORIAL_IS_WSL TUTORIAL_PKG

# Convenience: open a URL in the host's default browser. Used by deploy_and_test.sh.
tutorial_open_url() {
  local url="$1"
  if   command -v wslview     >/dev/null 2>&1; then wslview "$url" >/dev/null 2>&1
  elif command -v open        >/dev/null 2>&1 && [[ "$TUTORIAL_OS_FAMILY" == "macos" ]]; then open "$url"
  elif command -v xdg-open    >/dev/null 2>&1; then xdg-open "$url" >/dev/null 2>&1
  elif command -v sensible-browser >/dev/null 2>&1; then sensible-browser "$url" >/dev/null 2>&1 &
  else
    echo "[tutorial] open this URL manually: $url"
    return 1
  fi
}
