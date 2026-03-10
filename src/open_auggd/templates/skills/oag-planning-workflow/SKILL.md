---
name: oag-planning-workflow
description: Phase skill for planning work: turn exploration findings into a spec and one TDD-sized iteration with explicit acceptance criteria.
compatibility: opencode
---

# Planning Workflow

Phase: plan
Primary artifacts: `<WS>/plan/spec.md`, `<WS>/plan/iter-N-plan.md`,
`<WS>/plan/iter-N-plan.json`, `<WS>/plan/progress-log.json`

## What to do

1. Call `auggd tools plan --ws=<N> start` before writing any artifacts. This requires
   `explore_status = done` and creates the `plan/` directory structure. Idempotent.

2. Read `<WS>/explore/<topic>.md` files for context. Do not plan from memory.

3. Read `<WS>/plan/spec.md` if it exists. Understand current intent before changing it.

4. Decide the next step:
   - Write or update `spec.md` if the problem statement needs sharpening
   - Create a new iteration if the next behavior slice is clear
   - Revise an existing iteration if requirements changed
   - Route back to explore if key facts are still missing

5. Write or update `<WS>/plan/spec.md` using `oag-spec-template`. Keep it thin: intent,
   scenarios, constraints, non-goals. Not a design document.

6. Call `auggd tools plan --ws=<N> iter create` to allocate the next iteration number and
   create `iter-N-plan.json`.

7. Write `<WS>/plan/iter-N-plan.md` using `oag-iteration-template`. One iteration = one
   clear behavior slice, small enough for one RED → GREEN → REFACTOR loop.

8. Populate `acceptance_criteria` — specific, testable conditions that define done.
   This is required before `iter done` succeeds.

9. Call `auggd tools plan --ws=<N> iter done <N>` when the iteration is ready for
   development. This validates acceptance criteria are non-empty and sets status to
   `pending`.

## Required output per iteration

The `iter-N-plan.md` must contain:
- Objective (one sentence)
- Source scenarios (IDs from spec.md — e.g. S1, S2)
- In scope
- Out of scope
- Touch points (expected files / modules)
- Test plan
- Quality gates
- Stop and ask conditions
- Definition of done

The `iter-N-plan.json` (managed by `auggd tools plan`) must have non-empty
`acceptance_criteria` before `iter done` is called.

## Iteration sizing rules

- One iteration = one behavior change reviewable as a unit
- If the next step requires more than one failing test to describe, split it
- Front-load the riskiest or least-understood slice first
- Never batch "while I'm here" improvements into a planned iteration
- Fix cycles produce a new iteration number (iter-4, not a new iter-1)

## What NOT to do

- Do not start an iteration without calling `auggd tools plan --ws=<N> iter create`.
- Do not mark `iter done` without real acceptance criteria — vague criteria block
  meaningful review later.
- Do not widen scope "for completeness" — non-goals are as important as goals.
- Do not design the implementation — touch points and test plan are guidance, not
  architecture. Let the developer shape the implementation.
- Do not call `iter done` if the developer cannot begin without re-planning.

## Exit criteria

- `spec.md` reflects current intent
- Iteration is small, testable, and scoped
- `acceptance_criteria` non-empty in `iter-N-plan.json`
- Status set to `pending` via `auggd tools plan --ws=<N> iter done <N>`
- Developer can begin without asking clarifying questions about scope

## Handoff

To `oag-develop` when the iteration is implementation-ready.
Back to `oag-explore` if key facts are still missing or the approach is not settled.
