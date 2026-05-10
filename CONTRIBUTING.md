# Contributing

Thank you for considering a contribution. This repo is a tutorial,
which means each change is judged on **what a reader learns** rather
than what a maintainer ships.

## Before you open a PR

Answer these in the PR description:

1. **What concept does this teach?** A lesson with no concept is a
   code dump. Name it in one sentence.
2. **What failure mode does it prevent?** "Reader hits X confusion"
   or "reader writes Y broken pattern." If you can't name one, the
   change is an aesthetic — push back on yourself.
3. **What's the smallest version of this?** Tutorials drown in
   completeness. Cut until it stops teaching, then add one line back.
4. **Did you run it on Debian trixie + WSL2?** If no, say so. We'll
   verify before merge.

## Review rubric

Any reviewer (human or `Agent(subagent_type=...)`) checks:

- [ ] Builds with `colcon build --packages-select <pkg>` in isolation.
- [ ] Imports cleanly with no robot connected (`pytest tests/test_imports.py`).
- [ ] Smoke test added if the lesson has a runnable entry point.
- [ ] Walkthrough HTML updated if the lesson is reader-facing.
- [ ] Lesson table in `README.md` updated if a new package was added.
- [ ] No motion command path bypasses the `safety_engaged` latch.
- [ ] No new install dependency without bumping `install/*.sh`.

## Lesson template

```
ws/src/tutorial_<short_name>/
├── package.xml
├── setup.py
├── setup.cfg
├── resource/tutorial_<short_name>
└── tutorial_<short_name>/
    ├── __init__.py
    └── <entry_point>.py
```

`scripts/lesson_new.sh tutorial_<short_name>` (or the `/lesson-new`
slash command) scaffolds this.

## Style

- Python: PEP 8, 100-char line limit, type hints on public APIs,
  Google-style docstrings on lesson entry points (the docstring *is*
  the lesson summary the reader sees in `--help`).
- ROS messages: snake_case fields, comments only for units (`# m/s`).
- Bash: `set -euo pipefail` at the top, `[[` not `[`, quote everything.

## What we will close without merging

- Lessons that pull in heavy deps (tensorflow, torch) for a teaching
  point that doesn't need them.
- Production hardening that obscures the lesson concept.
- "Cleanups" that delete the educational redundancy. Three near-
  identical lesson packages is a feature, not a bug — the reader
  diffs them to learn.
- Any change that bypasses the safety latch on `g1_bridge`.
