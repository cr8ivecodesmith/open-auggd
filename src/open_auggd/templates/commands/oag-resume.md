---
name: oag-resume
description: Resume work on a workspace from the current phase. Reads artifact state and routes to the appropriate next action.
agent: auggd
model: opencode/gpt-5-nano
---

Workspace: `$1`
Iteration hint (optional): `$2`

Do:
1) Run `auggd ws info $1` for high-level workspace state.

2) Run `auggd tools explore --ws=$1 status`.

3) For each iteration visible in `ws info`, run:
   `auggd tools plan --ws=$1 iter status <N>`

4) If `$2` is provided or there is an iteration in active development or review:
   - Run `auggd tools develop --ws=$1 status $2` (or for the active iteration)
   - Run `auggd tools review --ws=$1 status $2` if applicable

5) Determine the current phase and state from the artifact reads:
   - Explore not done → continue explore
   - Explore done, no iterations planned → go to plan
   - Iteration pending (no devlog started) → go to develop
   - Iteration in_progress → continue develop
   - dev_complete → go to review
   - review changes_requested → return to develop
   - review approved → go to finalize
   - All iterations finalized → go to document (if changes warrant it) or done

6) If the next move is obvious and safe (one clear next phase), route to the appropriate
   subagent or command:
   - Continue explore → `@oag-explorer`
   - Go to plan → `@oag-planner`
   - Start or continue develop → `@oag-developer`
   - Start review → `@oag-reviewer`
   - Finalize approved iteration → `@oag-finalizer`
   - Update docs → `@oag-documenter`

7) If the state is ambiguous or requires a decision (e.g. multiple iterations at different
   phases, conflicting states), stop and output a concise decision summary:
   - What the current state is
   - What is blocking or ambiguous
   - What information is needed to proceed
   - Options for the user to choose from

8) Prefer the smallest viable next move. Do not batch phases.
