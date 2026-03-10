---
name: oag-finalize-workflow
description: Phase skill for finalize work: close out an approved iteration, update the progress log, and optionally commit changes.
compatibility: opencode
---

# Finalize Workflow

Phase: finalize
Primary artifact: `<WS>/plan/progress-log.json` (updated by `auggd tools finalize`)

## What to do

1. Call `auggd tools review --ws=<N> status <N>` to confirm review status is `approved`.
   Do not proceed if `changes_requested` or `blocked`. The finalize tool also enforces
   this gate, but confirm before calling.

2. Call `auggd ws info <N>` to see overall workspace state and confirm which iteration
   is being finalized.

3. Call `auggd tools finalize --ws=<N> iter <N>` to close out the iteration.
   - This sets `iter-N-plan.json` status to `finalized`
   - Updates `plan/progress-log.json`
   - If `--commit` is passed, runs `git add -A && git commit` with a generated message

4. If committing, pass `--commit` to the finalize call. The commit message is generated
   from the iteration title and status. Push and PR are manual user decisions after
   finalize — do not push unless explicitly instructed.

5. Confirm the result via `auggd ws info <N>`. Check that the iteration shows as
   finalized in the progress log.

6. Report the finalization summary to `auggd`: iteration number, finalized status,
   commit hash if committed, recommended next action.

## What NOT to do

- Do not finalize an iteration with `changes_requested` or `blocked` review status.
- Do not push to remote — push and PR are manual user decisions.
- Do not make code changes — finalize is a state transition, not a coding phase.
- Do not modify workspace artifacts beyond what `auggd tools finalize` does.
- Do not skip the review status check even though the tool enforces it — confirm first.

## After finalize

Finalize ends one TDD cycle. The workspace is ready for one of:
- A new iteration → back to `oag-plan`
- Documentation update → `oag-document`
- Both, if the completed work changes public-facing behavior or project structure

The user decides whether to push / open a PR. This is outside the `auggd` workflow.

## Exit criteria

- Iteration status `finalized` in `iter-N-plan.json`
- `progress-log.json` updated
- Commit made if `--commit` was requested
- No uncommitted changes to workspace artifacts

## Handoff

More iterations planned → to `oag-plan`
All iterations done and docs need updating → to `oag-document`
Work complete, no docs needed → end of loop
