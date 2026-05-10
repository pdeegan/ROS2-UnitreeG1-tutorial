"""Pytest config — pulls the workspace install onto sys.path so tests can
import packages without needing the colcon shell setup to be sourced.

Tests still pass when run from a plain `pytest` invocation, provided
`bash install/install.sh` has been run and `ws/install/` exists. If
the workspace hasn't been built yet, the package-import tests skip
themselves rather than fail noisily.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
WS_INSTALL = REPO_ROOT / "ws" / "install"


def _augment_sys_path() -> None:
    if not WS_INSTALL.exists():
        return
    # Each package installs to ws/install/<pkg>/lib/pythonX.Y/site-packages
    for pkg_dir in WS_INSTALL.iterdir():
        if not pkg_dir.is_dir():
            continue
        for lib in (pkg_dir / "lib").glob("python*/site-packages"):
            if str(lib) not in sys.path:
                sys.path.insert(0, str(lib))


_augment_sys_path()


def _unset_dds_profile_for_tests() -> None:
    """Tests should not assume any specific network interface exists.

    The default ``install/cyclonedds.xml`` profile binds to ``eth0`` (the
    expected interface when talking to a real Unitree G1). On a CI box
    or a dev laptop without that interface, the resulting DDS init
    fails with "does not match an available interface". Strip the env
    var so DDS falls back to auto-detect (loopback multicast for
    in-process tests).
    """
    for var in ("CYCLONEDDS_URI", "CYCLONEDDS_PROFILE"):
        os.environ.pop(var, None)


_unset_dds_profile_for_tests()


def pytest_configure(config) -> None:  # noqa: ANN001
    config.addinivalue_line(
        "markers", "hardware: requires a connected G1 robot (skipped by default)"
    )
    config.addinivalue_line(
        "markers", "ros_runtime: requires a running ROS 2 daemon"
    )
