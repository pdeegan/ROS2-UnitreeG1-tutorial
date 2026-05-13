#!/usr/bin/env bash
# walkthrough_smoke.sh — verify docs/walkthrough.html opens and the
# JS interactivity (copy buttons, search box, ref index) works headlessly.
#
# Usage:
#   bash tests/integration/walkthrough_smoke.sh
#
# Requires: chromium  (apt-get install -y chromium  on Debian)

set -uo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

GREEN='\033[0;32m'; RED='\033[0;31m'; NC='\033[0m'
PASS=0; FAIL=0
ok()   { PASS=$((PASS+1)); printf "  ${GREEN}✓${NC} %s\n" "$*"; }
fail() { FAIL=$((FAIL+1)); printf "  ${RED}✗${NC} %s\n" "$*"; }

CHROMIUM="$(command -v chromium || command -v chromium-browser || command -v google-chrome || true)"
if [[ -z "$CHROMIUM" ]]; then
  echo "chromium not installed; skipping (install with: sudo apt-get install -y chromium)"
  exit 0
fi

URL="file://$REPO_ROOT/docs/walkthrough.html"
DOM=/tmp/walkthrough_smoke_dom.html
ERR=/tmp/walkthrough_smoke_err.log

# Always render into a fresh profile dir so a stale /tmp/.org.chromium.*
# lock from a prior chromium instance (full_e2e leaves them around) can't
# silently produce an empty DOM. Clean up on exit.
PROFILE_DIR="$(mktemp -d -t walkthrough_smoke_chromium.XXXXXX)"
trap 'rm -rf "$PROFILE_DIR"' EXIT

echo "rendering: $URL"
# Strip LD_LIBRARY_PATH + PYTHONHOME + Conda/RoboStack env vars before
# launching chromium — otherwise the micromamba env's libminizip/libgio
# get loaded and chromium hits `undefined symbol:
# unzGetCurrentFileZStreamPos64`. This is invisible to a standalone
# invocation (no ROS env sourced) but reliably breaks Phase 8b of
# full_e2e.sh.
env -u LD_LIBRARY_PATH -u LD_PRELOAD -u PYTHONHOME -u PYTHONPATH \
    -u CONDA_PREFIX -u CONDA_DEFAULT_ENV -u MAMBA_ROOT_PREFIX \
    -u CMAKE_PREFIX_PATH -u AMENT_PREFIX_PATH -u COLCON_PREFIX_PATH \
  "$CHROMIUM" --headless --disable-gpu --no-sandbox \
    --user-data-dir="$PROFILE_DIR" \
    --enable-logging --v=0 \
    --virtual-time-budget=3000 \
    --dump-dom \
    "$URL" 2>"$ERR" 1>"$DOM"

if [[ ! -s "$DOM" ]]; then
  fail "empty DOM"
  echo "    chromium stderr: $(head -1 "$ERR" 2>/dev/null || echo '(empty)')"
  exit 1
fi
ok "DOM rendered ($(wc -c <"$DOM") bytes)"

# Per-block copy wrappers
n=$(grep -c 'class="codewrap"' "$DOM" || true)
[[ "$n" -ge 50 ]] && ok "$n codewrap divs (one per <pre>)" || fail "too few codewraps: $n"

# Block-level copy buttons
n=$(grep -c 'class="copy-btn"' "$DOM" || true)
[[ "$n" -ge 50 ]] && ok "$n block-copy buttons" || fail "too few block-copy buttons: $n"

# Per-line command copy wrappers
n=$(grep -c 'class="cmd-line"' "$DOM" || true)
[[ "$n" -ge 80 ]] && ok "$n per-line command wrappers" || fail "too few per-line wrappers: $n"

# Search infrastructure
grep -q 'id="search-input"' "$DOM" && ok "search input present" || fail "search input missing"
grep -q 'id="search-results"' "$DOM" && ok "search results container present" || fail "search results missing"
grep -q 'id="reference-index"' "$DOM" && ok "embedded reference index present" || fail "reference index missing"

# JS errors? Filter out unrelated chromium dbus / device noise — only catch
# real JS console.error / Uncaught exceptions / Promise rejections.
js_err=$(grep -E 'CONSOLE|Uncaught|Unhandled.*[Rr]ejection|SyntaxError|ReferenceError|TypeError' "$ERR" \
         | grep -vE 'dbus|DisplayDevice|UPower|DevTools|GPU process|sandbox' || true)
if [[ -n "$js_err" ]]; then
  fail "JS errors / exceptions in console:"
  echo "$js_err" | head -5 | sed 's/^/    /'
else
  ok "no JS errors (chromium dbus/device noise filtered)"
fi

# Reference index entry count (rough: count occurrences of "doc_title")
ref_count=$(grep -oE '"doc":"[^"]+"' "$DOM" | wc -l)
[[ "$ref_count" -ge 20 ]] && ok "$ref_count reference index entries embedded" \
                           || fail "too few reference entries: $ref_count"

printf "\nsummary: ${GREEN}%d passed${NC}, ${RED}%d failed${NC}\n" "$PASS" "$FAIL"
[[ "$FAIL" -eq 0 ]] && exit 0 || exit 1
