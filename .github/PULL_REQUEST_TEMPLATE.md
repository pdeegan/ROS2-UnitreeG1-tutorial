<!-- Thank you for opening a PR. -->

## What concept does this teach / change?

<!-- One sentence. If it's a lesson change, name the concept.
     If it's infrastructure, name what's now possible / safer / faster. -->

## What failure mode does it prevent?

<!-- "Reader hits X confusion" or "reader writes Y broken pattern."
     If you can't name one, push back on yourself before merging. -->

## How did you verify it?

- [ ] `bash scripts/ros2_build.sh` — workspace builds clean
- [ ] `pytest tests/test_imports.py tests/test_lessons.py -v` — all green
- [ ] `bash tests/integration/full_e2e.sh` — end-to-end pipeline green
- [ ] If reader-facing: `docs/walkthrough.html` updated + opened in a browser
- [ ] If new lesson: added to `README.md` table and `tests/test_lessons.py`

## Safety

- [ ] No motion command path bypasses the `/g1/safety_engaged` latch
- [ ] No default gain / torque change makes a first-run motion violent
- [ ] No new install dependency without bumping `install/*.sh`

## Anything else a reviewer should know?

<!-- Links to relevant issues, screenshots, alternative approaches you
     considered and dropped, etc. -->
