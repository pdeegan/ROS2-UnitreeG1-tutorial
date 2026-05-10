# .claude/ — Claude Code harness for the ROS 2 tutorial

This directory configures Claude Code (and any AGENTS.md-compatible
agent) for working on this repo.

## Layout

```
.claude/
├── settings.json              # permissions + hooks + statusline
├── README.md                  # this file
├── agents/                    # specialist subagents
│   ├── ros2-architect.md      # design lessons, topic topology
│   ├── ros-node-author.md     # write/edit rclpy nodes
│   ├── colcon-builder.md      # build errors, package.xml, setup.py
│   ├── wsl-setup-checker.md   # WSL/NVIDIA/CycloneDDS diagnosis
│   ├── unitree-integrator.md  # G1 SDK <-> ROS 2 boundary
│   └── tutorial-writer.md     # walkthrough + docs copy
├── commands/                  # /ros-* slash commands
│   ├── ros-bringup.md         # bring up the env in current shell
│   ├── ros-build.md           # colcon build with diagnostics
│   ├── ros-doctor.md          # run scripts/doctor.sh
│   ├── ros-review.md          # parallel multi-agent review
│   ├── lesson-new.md          # scaffold a new lesson
│   └── lesson-test.md         # build + smoke-test one lesson
└── scripts/
    ├── session_start.sh       # status banner on session start
    ├── post_edit_verify.sh    # syntax check edited Python files
    └── statusline.sh          # custom statusline
```

## How to use the agents

The agents are picked **by task match** — when you ask Claude to do
something that fits the description, it'll auto-invoke. You can also
force one explicitly with `Agent(subagent_type="ros-node-author")`.

| Task | Agent |
|---|---|
| "Add a new lesson on QoS profiles" | `ros2-architect` then `ros-node-author` |
| "This `colcon build` is failing" | `colcon-builder` |
| "Why does CycloneDDS not see the robot?" | `wsl-setup-checker` |
| "Add a topic that bridges `LowState`" | `unitree-integrator` |
| "Polish the lesson 04 copy" | `tutorial-writer` |

`/ros-review` dispatches `ros2-architect`, `colcon-builder`, and
`tutorial-writer` in parallel against the current diff.

## Hooks

- **SessionStart** prints a one-line health summary (env discovered?
  workspace built? robot reachable?) so Claude can pick up cold.
- **PostToolUse on Edit/Write** runs a `python -m py_compile` over
  any `.py` you just touched. Cheap, catches dumb syntax errors
  before the next `colcon build` does.
