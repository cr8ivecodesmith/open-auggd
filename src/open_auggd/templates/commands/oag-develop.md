---
name: oag-develop
description: Run the develop phase for one iteration. Implement using strict TDD, update the devlog, and mark dev_complete when done. No commit.
agent: oag-developer
subtask: true
model: opencode/gpt-5-nano
---

Workspace: `$1`
Iteration: `$2`

Do:
1) Load skills: `oag-development-workflow`, `oag-devlog-template`, `oag-tdd-standards`

2) Run `auggd tools develop --ws=$1 status $2` to check current devlog state.

3) Read the workspace `plan/iter-$2-plan.md` for what to implement — scope, acceptance
   criteria, touch points, and stop conditions. Do not proceed without reading it.

4) Read the workspace `plan/spec.md` for overall intent and constraints.

5) If resuming after review changes, read the workspace `review/iter-$2-review.md` for
   the specific findings to address.

6) If resuming a prior session, read the tail of the workspace `develop/iter-$2-devlog.md`
   for the last known state and next step.

7) Run `auggd tools develop --ws=$1 start $2` if not yet started.

8) Implement in strict RED → GREEN → REFACTOR:
   - Write the next failing test first
   - Write the minimum code to pass it
   - Refactor safely under green
   - Repeat until all acceptance criteria are addressed

9) After each meaningful step, update structured state:
   `auggd tools develop --ws=$1 update $2 --data '{"files_touched": [...], "tests_run": [...], "next_red_step": "..."}'`

10) Append a narrative entry to the workspace `develop/iter-$2-devlog.md` following
    `oag-devlog-template`.

11) Run quality gates: tests, lint, typecheck. Record results in the devlog and via update.
    Do not proceed to done if any gate fails.

12) Run `auggd tools develop --ws=$1 done $2` when the cycle is complete and gates pass.
    Do not commit.

13) Summarize what was implemented: files touched, tests run, scenarios addressed, gate results.
    Suggested follow-on: `/oag-review $1 $2`
