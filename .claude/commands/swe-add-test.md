---
description: Write a failing test for a bug or new behavior, BEFORE the production code changes. Hands off to regression-test-writer. Returns the test code and the failure output, not the production fix.
argument-hint: <bug-description-or-issue-link>
allowed-tools: Bash, Read, Edit, Write, Agent
model: inherit
---

The kit's files that this names (the five protocols, CRAFT.md, ADR_TEMPLATE.md, and anything under scripts/ or tools/) are in /home/code0x19/SOFTWARE/agent-alignment/swe, whichever project you are in.

Write a failing test that reproduces the named bug (or specifies
the new behavior).

Input: `$ARGUMENTS` is the bug description, the issue link, or a
quoted user-report. If empty, ask the user for the failing
observation.

Steps:

1. Spawn `regression-test-writer` with the bug description. Brief:
   "reproduce as a failing test in the closest existing test file
   using the project's existing fixtures. Confirm it fails on the
   pre-fix code. Report file path, the test code, and the failure
   output. Do not write the production fix."
2. Surface the test, the failure output, and the suspected bug
   source (file:line) to the user.
3. Recommend the next step: either the user implements the fix,
   or the user names a specialist (`debugger` for diagnosis,
   `code-reviewer` for the fix review).

Do not commit. Do not write the production fix from this command.
