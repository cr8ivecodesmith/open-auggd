---
name: oag-development-workflow
description: Phase skill for development work: implement one planned iteration with strict TDD, maintain the devlog, and mark dev_complete when the cycle is done.
compatibility: opencode
---

# Development Workflow

Phase: develop
Primary artifacts: `<WS>/develop/iter-N-devlog.md`, `<WS>/develop/iter-N-devlog.json`

## What to do

1. Call `auggd tools develop --ws=<N> status <N>` to check current devlog state before
   starting or resuming.

2. Read `<WS>/plan/iter-N-plan.md` for what to implement. Do not proceed without reading
   the iteration plan — it defines scope, acceptance criteria, and stop conditions.

3. Read `<WS>/plan/spec.md` for overall intent and constraints.

4. If resuming after a review with changes: read `<WS>/review/iter-N-review.md` for the
   specific findings to address.

5. If resuming a prior session: read the tail of `<WS>/develop/iter-N-devlog.md` for
   context and the last known next step.

6. Call `auggd tools develop --ws=<N> start <N>` to initialize devlog artifacts. Idempotent
   if already started. Requires `iter-N-plan.json` to exist with status `pending` or
   `in_progress`.

7. Implement in strict RED → GREEN → REFACTOR slices:
   - Write the next failing test first
   - Write the minimum code to make it pass
   - Refactor under green — do not expand scope

8. After each meaningful step, call:
   `auggd tools develop --ws=<N> update <N> --data '<json>'`
   with fields: `files_touched`, `tests_run`, `blockers`, `next_red_step`

9. Append a narrative entry to `<WS>/develop/iter-N-devlog.md` using `oag-devlog-template`.

10. Run quality gates: tests, lint, typecheck. Record results in the devlog and in
    `auggd tools develop update`.

11. Call `auggd tools develop --ws=<N> done <N>` when the cycle is complete and gates pass.
    Do not commit. Do not push.

## Required devlog update fields

When calling `auggd tools develop --ws=<N> update <N> --data`:

```json
{
  "files_touched": ["path/to/file.py"],
  "tests_run": [{"command": "pytest tests/", "result": "5 passed"}],
  "next_red_step": "write test for edge case X",
  "blockers": []
}
```

List fields (`files_touched`, `tests_run`, `blockers`) are extended on each update.
Scalar fields replace the previous value. `status` and `n` are protected — do not include.

## What NOT to do

- Do not widen scope — if new work appears, record it as a future iteration note, not
  current implementation.
- Do not commit — committing is the finalizer's responsibility after review approval.
- Do not skip devlog updates — the reviewer needs the devlog to understand what changed
  and why.
- Do not call `done` if quality gates are failing.
- Do not invent new architecture — follow the touch points in the iteration plan; ask
  `oag-explorer` if genuinely lost in the repo.
- Do not start without calling `start` — the tool initializes the JSON counterpart.

## When to pause and ask

Stop and route back if:
- The next step requires touching surfaces explicitly listed as out of scope
- A migration, public contract change, or security decision appears
- New requirements surface that weren't in the iteration plan
- A fix requires touching many unrelated surfaces

## Exit criteria

- All acceptance criteria from `iter-N-plan.json` addressed
- Tests green
- Quality gates pass (lint, typecheck)
- Devlog reflects what happened (files, tests, next step)
- `dev_complete` set via `auggd tools develop --ws=<N> done <N>`

## Handoff

To `oag-review` when cycle is complete and gates pass.
Back to `oag-plan` if scope changed significantly or the iteration plan is wrong.
Back to `oag-explore` if key facts are genuinely missing.
