---
name: oag-iteration-template
description: Template and structure for iter-N-plan.md — the narrative iteration plan companion to iter-N-plan.json.
compatibility: opencode
---

# Iteration Template

Artifact: `<WS>/plan/iter-N-plan.md`
JSON counterpart: `<WS>/plan/iter-N-plan.json` (managed by `auggd tools plan`)
Type: rewritten as understanding of the iteration evolves before development starts

## Sizing rules

One iteration = one TDD-sized behavior slice:
- One clear behavioral intention expressible in one sentence
- Small enough for one RED → GREEN → REFACTOR loop
- Explicit stop conditions — the developer knows when to stop
- Reviewable as a unit — reviewer can understand intent and verify it

If the iteration cannot be described in one sentence objective, split it.
If the test plan requires more than 5 new test cases, split it.
If touch points span more than 3–4 files, consider splitting.

## Iteration numbering

Iteration numbers are globally monotonic per workspace. A fix cycle produces `iter-4`,
not a new `iter-1`. `auggd tools plan --ws=<N> iter create` assigns the next number.

## Template

```markdown
# Iteration <N> — <Short Title>

## Status
- Workspace: <workspace-id>
- Iteration: <N>
- Status: pending | in_progress | dev_complete | review_complete | finalized

## Objective
<One sentence. What behavior does this iteration add or change?>

## Source scenarios
Scenario IDs from spec.md that this iteration addresses.
- [ ] S1 — <title>
- [ ] S2 — <title>

## In scope
- <specific behavior 1>
- <specific behavior 2>

## Out of scope
- <explicit exclusion — prevents scope creep during development>
- <explicit exclusion>

## Touch points
Expected files, modules, or surfaces that will change. Not exhaustive — the developer
may find other surfaces, but should stop and ask if they significantly diverge.
- `src/module/file.py` — <what changes and why>
- `tests/unit/test_file.py` — <what tests are added>

## Test plan
Tests to add or update. Be specific enough that a developer can write the first failing
test without guessing.
- Test that <behavior under happy path>
- Test that <behavior under error condition>
- Test that <edge case>

## Quality gates
- [ ] All tests green (`pytest tests/`)
- [ ] Lint passes (`ruff check src/`)
- [ ] Typecheck passes (`mypy src/`) — if applicable
- [ ] <project-specific gate if any>

## Stop and ask if
The developer should pause and route back to planning if:
- <trigger 1 — e.g. "implementation requires touching authentication logic">
- <trigger 2 — e.g. "a new public API surface is needed">
- The next step is larger than one RED → GREEN cycle

## Definition of done
- [ ] Behavior implemented per objective
- [ ] All source scenarios addressed (checked above)
- [ ] Quality gates pass
- [ ] No unapproved scope expansion
- [ ] Devlog reflects what was done
- [ ] Ready for review

## Notes
<Any context, decisions, or references the developer should know about.>
```

## Writing guidance

**Objective**: must be one sentence. If you need two sentences, the iteration covers two
behaviors — split it.

**Source scenarios**: link to scenario IDs from `spec.md`. A reviewer uses these to verify
that the implementation addresses the right scenarios. Every scenario addressed should
appear here.

**In scope vs. out of scope**: the developer will encounter temptations. Explicit out-of-scope
entries prevent "while I'm here" expansion. If something belongs in a future iteration,
say so.

**Touch points**: help the developer orient without over-specifying. They are guidance, not
architecture. If the developer finds the real implementation requires different surfaces,
they should flag it via stop-and-ask, not silently expand.

**Test plan**: specific enough to write the first failing test. "Test error handling" is not
enough. "Test that calling `ws delete` with an out-of-range number raises a clear error" is.

**Stop and ask**: this is the developer's escape hatch. Be honest about what would signal
that the iteration plan is wrong. Better to surface this before implementation than
mid-cycle.

## Relationship to iter-N-plan.json

The JSON counterpart tracks `status`, `acceptance_criteria`, `scope`, and timestamps.
`auggd tools plan --ws=<N> iter done <N>` requires `acceptance_criteria` to be non-empty.
The markdown narrative provides the human-readable context. Keep both consistent.
