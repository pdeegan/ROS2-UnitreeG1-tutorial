#!/usr/bin/env bash
# 04_unitree_sdk.sh — verify Unitree SDK Python bindings are present.
# Does NOT pip install if missing — that's a deliberate user decision
# (the SDK download is large and version-sensitive). Prints next steps.
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
log()  { printf "[04_unitree_sdk] %s\n" "$*"; }
warn() { printf "[04_unitree_sdk] WARN: %s\n" "$*"; }

# shellcheck source=/dev/null
source "$SCRIPT_DIR/.discovered.sh"
MAMBA_BIN="$TUTORIAL_MAMBA_BIN"
ENV_DIR="$TUTORIAL_ROS_ENV"
export MAMBA_ROOT_PREFIX="$TUTORIAL_MAMBA_ROOT"
RUN=( "$MAMBA_BIN" run -p "$ENV_DIR" python )

if "${RUN[@]}" -c "import unitree_sdk2py" 2>/dev/null; then
  ver=$("${RUN[@]}" -c "import importlib.metadata as m; print(m.version('unitree-sdk2py'))" 2>/dev/null || echo "unknown")
  log "unitree_sdk2py present (v$ver)."
else
  warn "unitree_sdk2py NOT importable in $ENV_DIR"
  warn "to add it (the bridge package depends on it, lessons 07-09 require it):"
  warn "  $MAMBA_BIN run -p $ENV_DIR python -m pip install unitree-sdk2py"
  warn "or from source:"
  warn "  git clone https://github.com/unitreerobotics/unitree_sdk2_python.git"
  warn "  $MAMBA_BIN run -p $ENV_DIR python -m pip install -e ./unitree_sdk2_python"
fi

if "${RUN[@]}" -c "import cyclonedds" 2>/dev/null; then
  log "cyclonedds Python binding present."
else
  warn "cyclonedds Python binding missing — the bridge package will fail at import."
fi

CYCLONE_XML="$REPO_ROOT/install/cyclonedds.xml"
if [[ -f "$CYCLONE_XML" ]]; then
  log "CycloneDDS profile already at $CYCLONE_XML"
else
  log "writing CycloneDDS profile → $CYCLONE_XML"
  cat > "$CYCLONE_XML" <<'XML'
<?xml version="1.0" encoding="UTF-8"?>
<!--
  CycloneDDS profile for the Unitree G1 bridge.
  Edit name="eth0" to match your robot-facing interface (run `ip -br addr`).
-->
<CycloneDDS xmlns="https://cdds.io/config" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
            xsi:schemaLocation="https://cdds.io/config https://raw.githubusercontent.com/eclipse-cyclonedds/cyclonedds/master/etc/cyclonedds.xsd">
  <Domain Id="any">
    <General>
      <Interfaces>
        <NetworkInterface autodetermine="false" name="eth0" priority="default" multicast="default" />
      </Interfaces>
      <AllowMulticast>true</AllowMulticast>
      <MaxMessageSize>65500B</MaxMessageSize>
    </General>
    <Internal>
      <Watermarks>
        <WhcHigh>500kB</WhcHigh>
      </Watermarks>
    </Internal>
  </Domain>
</CycloneDDS>
XML
fi

log "set this before running G1 lessons against the real robot:"
log "  export CYCLONEDDS_URI=file://$CYCLONE_XML"
