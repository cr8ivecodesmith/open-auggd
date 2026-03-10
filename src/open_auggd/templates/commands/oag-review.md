---
name: oag-review
description: Review one iteration for intent alignment, engineering quality, and test coverage. Produce structured findings and a final verdict.
agent: oag-reviewer
subtask: true
model: opencode/gpt-5-nano
---

Workspace: `$1`
Iteration: `$2`

Do:
1) Load skills: `oag-review-workflow`, `oag-review-template`

2) Run `auggd tools develop --ws=$1 status $2` to confirm `dev_complete`.
   If not dev_complete, stop and instruct the user to run `/oag-develop $1 $2` first.

3) Read the workspace `plan/iter-$2-plan.md` — what was intended, acceptance criteria,
   non-goals.

4) Read the workspace `plan/spec.md` — overall intent and constraints.

5) Read the workspace `develop/iter-$2-devlog.md` — what was done and why.

6) Inspect the changed files. Use git diff to identify the scope of changes.

7) Run `auggd tools review --ws=$1 start $2`.

8) Perform **Pass 1 — Intent alignment**:
   - Does the implementation address the scoped behavior from the iteration plan?
   - Did it stay in scope? Check non-goals explicitly.
   - Are tests aligned with acceptance criteria?
   - Is anything from the iteration plan missing?

9) Perform **Pass 2 — Engineering smell pass**:
   - Redundant, dead, or unreachable code
   - Superfluous complexity or abstraction tax
   - Performance footguns
   - Consistency and maintainability drift
   - Brittle or low-value tests
   - Risk hotspots: security, data/contracts, operability

10) Write the workspace `review/iter-$2-review.md` following `oag-review-template`.

11) Record each finding:
    `auggd tools review --ws=$1 update $2 --data '{"findings": [...]}'`
    Use severity: `MUST-FIX`, `SHOULD-FIX`, or `NICE-TO-HAVE`.

12) Run `auggd tools review --ws=$1 done $2 <status>` with:
    - `approved` — no MUST-FIX items
    - `changes_requested` — MUST-FIX or critical SHOULD-FIX items present
    - `blocked` — planning mistake, cannot proceed without re-planning

13) Summarize: verdict, finding counts by severity, and recommended next smallest step.
    If approved: suggested follow-on: `/oag-finalize $1 $2`
    If changes_requested: suggested follow-on: `/oag-develop $1 $2`
    If blocked: suggested follow-on: `/oag-plan $1`
