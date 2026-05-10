#!/usr/bin/env bash
# lesson_new.sh — scaffold a new ament_python tutorial package.
# Usage: bash scripts/lesson_new.sh tutorial_my_lesson
set -euo pipefail
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
NAME="${1:-}"
[[ -z "$NAME" ]] && { echo "usage: $0 <package_name>" >&2; exit 1; }
[[ "$NAME" =~ ^[a-z][a-z0-9_]*$ ]] || { echo "package name must be snake_case" >&2; exit 1; }

DST="$REPO_ROOT/ws/src/$NAME"
[[ -e "$DST" ]] && { echo "$DST already exists" >&2; exit 1; }
mkdir -p "$DST/$NAME" "$DST/resource" "$DST/test"
touch "$DST/resource/$NAME"

cat > "$DST/package.xml" <<XML
<?xml version="1.0"?>
<package format="3">
  <name>$NAME</name>
  <version>0.1.0</version>
  <description>Tutorial lesson: $NAME</description>
  <maintainer email="you@example.com">Tutorial</maintainer>
  <license>MIT</license>

  <depend>rclpy</depend>
  <depend>std_msgs</depend>

  <test_depend>ament_copyright</test_depend>
  <test_depend>ament_flake8</test_depend>
  <test_depend>ament_pep257</test_depend>
  <test_depend>python3-pytest</test_depend>

  <export>
    <build_type>ament_python</build_type>
  </export>
</package>
XML

cat > "$DST/setup.py" <<PY
from setuptools import find_packages, setup

package_name = "$NAME"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages",
         ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="Tutorial",
    maintainer_email="you@example.com",
    description="Tutorial lesson: $NAME",
    license="MIT",
    entry_points={
        "console_scripts": [
            "hello = ${NAME}.hello:main",
        ],
    },
)
PY

cat > "$DST/setup.cfg" <<CFG
[develop]
script_dir=\$base/lib/$NAME
[install]
install_scripts=\$base/lib/$NAME
CFG

cat > "$DST/$NAME/__init__.py" <<'PY'
"""Tutorial package."""
PY

cat > "$DST/$NAME/hello.py" <<'PY'
"""Lesson entry point — replace with the actual lesson content."""
import rclpy
from rclpy.node import Node


class HelloNode(Node):
    def __init__(self) -> None:
        super().__init__("hello")
        self.get_logger().info("hello from a fresh lesson scaffold")


def main(args: list[str] | None = None) -> None:
    rclpy.init(args=args)
    node = HelloNode()
    try:
        rclpy.spin_once(node, timeout_sec=0.1)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
PY

echo "scaffolded $DST"
echo "next:"
echo "  edit ws/src/$NAME/$NAME/hello.py"
echo "  cd ws && colcon build --packages-select $NAME"
echo "  ros2 run $NAME hello"
