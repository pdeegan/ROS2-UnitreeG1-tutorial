# Security Policy

This tutorial connects to a 35 kg humanoid robot. Vulnerabilities here
are not just data-integrity issues — they can cause physical harm.

## Reporting a vulnerability

If you find a bug that could result in the robot moving when the safety
latch is disengaged, in a stale or forged `lowcmd` reaching the SDK, or
in network-discoverable services that an attacker on the local segment
could call without authentication, please report it privately.

- Email: `security@teddybot.ai`
- Or open a private security advisory on GitHub:
  https://github.com/pdeegan/ROS2-UnitreeG1-tutorial/security/advisories/new

Please **do not** open a public issue for safety-impacting bugs until a
fix is available. We aim to acknowledge reports within 72 hours.

## What counts as in-scope

- Any code path that publishes `/g1/lowcmd` or forwards to the SDK's
  `rt/lowcmd` without the `/g1/safety_engaged` latch.
- Any lifecycle or service that allows a remote caller to bypass the
  documented safety contract.
- Hard-coded credentials, secrets, or robot IPs that would help an
  attacker on the same network segment.
- Install scripts that download executables over plain HTTP or without
  integrity verification.

## What is out of scope

- The tutorial's pedagogical scaffolding (deliberately minimal
  controllers, simple gains). These are documented as such in
  `docs/unitree_g1.md` under "Pedagogical scope, not production stack."
- Third-party assets fetched by `install/06_fetch_g1_assets.sh`
  (Unitree G1 URDF + meshes). Report upstream at
  https://github.com/unitreerobotics/unitree_ros.
- DDS / ROS 2 framework vulnerabilities. Report those to the
  CycloneDDS or ROS 2 security teams directly.

## The safety contract

The non-negotiable invariants of this repo:

1. Every motion-command path must check `/g1/safety_engaged` before
   publishing. The check sits on the publish side, not the application
   side, so a bug in `g1_controller` still fails closed.
2. The safety latch defaults to disengaged on startup. Engaging it
   requires an explicit service call.
3. Default torques and gains in lesson code must be conservative.
   A reader running an example for the first time should not see
   violent motion.

A PR that weakens any of these is treated as a security regression
and will be reverted.
