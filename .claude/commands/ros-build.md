---
description: Build the colcon workspace, with `--packages-select` if an argument is passed. Hands a build failure to colcon-builder.
argument-hint: [package-name]
allowed-tools: Bash, Agent, Read
model: inherit
---

Build the workspace.

```bash
source scripts/ros2_env.sh
cd ws
if [[ -n "$1" ]]; then
  colcon build --packages-select "$1"
else
  colcon build
fi
```

If the build fails, dispatch the `colcon-builder` agent with the
package name and the last 80 lines of output. If it succeeds, list
the entry points for the built package(s):

```bash
source ws/install/setup.bash
ros2 pkg executables ${1:-}
```
