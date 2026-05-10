---
description: Parallel multi-agent review of the current diff (ros2-architect, colcon-builder, unitree-integrator, tutorial-writer). Each returns a punch list; the main thread synthesizes findings without merging.
argument-hint: [base-branch]
allowed-tools: Bash, Read, Agent
model: inherit
---

Five-way parallel review of the diff against `$1` (default `main`).

Capture the diff first:

```bash
git diff "${1:-main}"...HEAD --stat
git diff "${1:-main}"...HEAD
```

Dispatch all four agents **in parallel** in a single message:

1. `ros2-architect` — does the change respect the topology + climb?
2. `colcon-builder` — will it build clean on every package
   independently?
3. `unitree-integrator` — does anything touch motion or safety latch?
4. `tutorial-writer` — does the walkthrough + docstrings still match
   the code?

Each agent receives the same brief: "Review the diff between
`${1:-main}` and HEAD. Output findings only — do not modify code."

After all four return, synthesize:
- A deduplicated severity-sorted finding list.
- Conflicts (where one says fix-X and another says X is fine).
- Final recommendation: SHIP / SHIP-WITH-NOTE / BLOCK.

Do not merge, fix, or rewrite. Hand the synthesis back to the user.
