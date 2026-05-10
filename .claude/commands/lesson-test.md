---
description: Build one lesson package, then run its smoke test. Equivalent to `bash scripts/run_tutorial.sh <N>` plus pytest.
argument-hint: <lesson-number-or-package>
allowed-tools: Bash, Read
model: inherit
---

Build + smoke-test one lesson.

```bash
source scripts/ros2_env.sh

# Resolve package name (lesson number or explicit name)
case "$1" in
  01|1) PKG=tutorial_basics    ;;
  02|2) PKG=tutorial_pubsub    ;;
  03|3) PKG=tutorial_services  ;;
  04|4) PKG=tutorial_actions   ;;
  05|5) PKG=tutorial_lifecycle ;;
  06|6) PKG=tutorial_tf        ;;
  07|7) PKG=g1_bridge          ;;
  08|8) PKG=g1_speech          ;;
  09|9) PKG=g1_controller      ;;
  *)    PKG="$1" ;;
esac

(cd ws && colcon build --packages-select "$PKG")
source ws/install/setup.bash
pytest "tests/test_lessons.py::test_${PKG}" -v -x
```

Report build status, import status, and pytest result.
