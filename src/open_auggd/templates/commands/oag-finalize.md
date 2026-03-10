---
name: oag-finalize
description: Finalize an approved iteration. Mark it complete, update the progress log, and optionally commit.
agent: oag-finalizer
subtask: true
model: opencode/gpt-5-nano
---

Workspace: `$1`
Iteration: `$2`

Do:
1) Load skills: `oag-finalize-workflow`

2) Run `auggd tools review --ws=$1 status $2` to confirm review status is `approved`.
   If not approved (status is `changes_requested` or `blocked`), stop and report the
   current review status. Do not proceed.

3) Run `auggd ws info $1` to confirm the overall workspace state.

4) Run `auggd tools finalize --ws=$1 iter $2`

   If the user explicitly requested a commit (e.g. "finalize and commit"), add `--commit`:
   `auggd tools finalize --ws=$1 iter $2 --commit`

   Do not add `--commit` unless explicitly instructed.

5) Verify finalization: run `auggd ws info $1` and confirm the iteration shows as
   `finalized` in the progress log.

6) Report the result:
   - Iteration number and title
   - Finalization confirmed (and commit hash + message if committed)
   - Recommended next action

   If more iterations are planned: suggested follow-on: `/oag-plan $1`
   If docs need updating: suggested follow-on: `/oag-document`
   Push and PR are manual user decisions — mention they are available but do not suggest
   them as part of the workflow.
