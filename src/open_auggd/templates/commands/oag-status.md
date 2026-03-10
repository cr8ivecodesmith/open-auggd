---
name: oag-status
description: Show the current state of a workspace — phase, artifact status, iteration summary, and next recommended action.
agent: oag-auggd
model: opencode/gpt-5-nano
---

Workspace: `$1`

Do:
1) Run `auggd ws info $1` for high-level workspace state: iterations, current phase,
   spec description.

2) Run `auggd tools explore --ws=$1 status` to get explore phase status.

3) For each iteration visible in `ws info`:
   - Run `auggd tools plan --ws=$1 iter status <N>` for plan state
   - Run `auggd tools develop --ws=$1 status <N>` if iteration is in develop or beyond
   - Run `auggd tools review --ws=$1 status <N>` if iteration is in review or beyond

4) Determine the current phase from the collected artifact states:
   - No explore done → explore phase
   - Explore done, no iterations → plan phase
   - Iteration in_progress or pending → develop phase
   - dev_complete → review phase
   - review approved → finalize phase
   - All iterations finalized → document or done

5) Identify:
   - Missing or incomplete artifacts
   - Any stale state (e.g. dev_complete but review not started)
   - Whether the workspace is blocked, ready to proceed, or needs routing

6) Output a concise status report:
   - Current phase
   - Iterations: counts and status of each
   - Biggest blocker or gap (if any)
   - Next recommended command

   Do not modify any files.
