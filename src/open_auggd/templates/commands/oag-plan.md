---
name: oag-plan
description: Run the plan phase for a workspace. Create or refine the spec and shape one TDD-sized iteration with acceptance criteria.
agent: oag-planner
subtask: true
model: opencode/gpt-5-nano
---

Workspace: `$1`
Requested iteration or focus (optional): `$2`

Do:
1) Load skills: `oag-planning-workflow`, `oag-spec-template`, `oag-iteration-template`,
   `oag-tdd-standards`

2) Run `auggd tools explore --ws=$1 status` to confirm exploration is done.
   If not done, stop and instruct the user to run `/oag-explore $1` first.

3) Run `auggd ws info $1` to check current plan state and any existing iterations.

4) Read the exploration narratives in the workspace `explore/` directory to understand
   the problem and candidate approaches.

5) If `$2` specifies an existing iteration number, run:
   `auggd tools plan --ws=$1 iter status $2`
   to load the current iteration state.

6) Decide the next step:
   - Write or update `plan/spec.md` if the problem statement needs sharpening
   - Create a new iteration if the next behavior slice is clear
   - Revise an existing iteration if requirements changed
   - Route back to explore if key facts are still missing

7) Run `auggd tools plan --ws=$1 start` if the plan phase has not been started.

8) Write or update the workspace `plan/spec.md` following `oag-spec-template`.

9) To create a new iteration:
   a) Run `auggd tools plan --ws=$1 iter create`
   b) Write the `plan/iter-N-plan.md` following `oag-iteration-template`
   c) Ensure acceptance criteria are specific and testable

10) Run `auggd tools plan --ws=$1 iter done <N>` when the iteration is ready for
    development.

11) Summarize what was planned: spec state, iteration number and objective, acceptance
    criteria, recommended next move.
    Suggested follow-on: `/oag-develop $1 <N>`
