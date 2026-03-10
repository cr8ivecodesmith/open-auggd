---
name: oag-tdd-standards
description: Pragmatic TDD standards for auggd-managed development: RED-GREEN-REFACTOR, behavior-driven slicing, and scope discipline.
compatibility: opencode
---

# TDD Standards

## Core loop

```
RED → GREEN → REFACTOR
```

1. **RED** — write the next failing test for the smallest describable behavior change
2. **GREEN** — write the minimum code to make the test pass; nothing more
3. **REFACTOR** — improve structure while tests stay green; do not expand scope

> "If the next step cannot be described in one sentence, it is too large. Slice thinner."

## What to test

Test behavior, not code shape:
- User-visible or business-observable outcomes
- Meaningful state changes
- Public interface contracts

Do not test:
- Internal implementation details that can change without breaking behavior
- Private methods or internal data structures
- Framework internals

## Test level

Start from the highest useful seam:
- New user-facing behavior → test from the command / API / domain service boundary
- Contained algorithm or bugfix → test closer to the function

Good heuristic: if the test would survive a complete internal refactor without changing, it
is testing the right thing.

## Iteration sizing

An iteration is one TDD-sized behavior slice:
- One clear behavioral intention
- A small number of related tests
- One bounded implementation step
- One reviewable change set

Signs an iteration is too large:
- More than one distinct "failing test first" story
- The test plan requires more than 3–5 new test cases
- The implementation touches more surfaces than listed in touch points
- You cannot explain the iteration goal in one sentence

## Test doubles

Use deliberately. Choose the lightest tool that proves the behavior:

| Double | When to use |
|---|---|
| Dummy | parameter filler, not used |
| Stub | returns canned values, no verification |
| Fake | working implementation, simplified (e.g. in-memory DB) |
| Spy | records calls for later assertion |
| Mock | pre-programmed with expectations, verified |

Avoid:
- Mocking objects that are cheap to create for real
- Mocking internal collaborators (tests the wiring, not the behavior)
- Layering mocks until only mocks are proven

## Design discipline

Let tests shape the design:
- Difficulty writing a test signals a design problem — fix the design, not the test
- Do not invent layers or abstractions in anticipation of future use
- Do not front-load generic infrastructure before specific behavior is proven
- Do not clean up unrelated code in the same iteration

## Scope discipline

Pause and route back to plan if:
- The next step requires touching surfaces listed as out of scope
- A migration or public contract change appears
- New requirements surface that were not in the iteration plan
- A "simple fix" touches many unrelated surfaces
- The test suite needs restructuring before the next step is possible

## Quality gates

Before marking dev_complete, run:
1. Full test suite — all tests green
2. Lint — no new lint errors
3. Typecheck (if applicable) — no new type errors

All gates must pass. Do not mark dev_complete with known failures.

## Anti-patterns

- Writing implementation before writing a failing test
- Writing tests after the implementation is complete
- Broad refactors without test protection
- "While I'm here" scope expansion
- Speculative wrappers, repos, or abstractions not required by the current behavior
- Mock-heavy tests that verify only choreography, not outcomes

## Exit test

The TDD cycle is healthy when:
- The next RED step is usually obvious
- Each change is small and explainable
- Tests describe behavior, not implementation
- The design feels earned, not invented
- The iteration is easy to review as a unit
