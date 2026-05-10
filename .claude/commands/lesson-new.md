---
description: Scaffold a new ament_python tutorial package via scripts/lesson_new.sh.
argument-hint: <package_name>
allowed-tools: Bash, Read, Agent
model: inherit
---

Scaffold a new tutorial package.

```bash
bash scripts/lesson_new.sh "$1"
```

After scaffolding, dispatch `ros2-architect` to produce a design for
the lesson (no code yet). Hand the design back to the user for
review before implementation begins.
