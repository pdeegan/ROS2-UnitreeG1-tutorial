---
description: Bring up the ROS 2 env in the current shell — sources scripts/ros2_env.sh and prints the discovered topology. Idempotent.
allowed-tools: Bash
model: inherit
---

Source the environment and print a one-line status.

```bash
source scripts/ros2_env.sh
ros2 --help | head -1
ros2 daemon status || true
```

Report back ROS_DISTRO, the env path, and any topics already
published (`ros2 topic list | head -10`).
