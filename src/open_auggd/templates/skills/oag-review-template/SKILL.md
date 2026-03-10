---
name: oag-review-template
description: Template and structure for iter-N-review.md — the narrative review document companion to iter-N-review.json.
compatibility: opencode
---

# Review Template

Artifact: `<WS>/review/iter-N-review.md`
JSON counterpart: `<WS>/review/iter-N-review.json` (managed by `auggd tools review`)
Type: rewritten per review pass — not append-only

## Severity levels

Every finding must have one of:
- `MUST-FIX` — blocks approval; correctness, security, or significant quality issue
- `SHOULD-FIX` — strong recommendation; maintainability or risk concern that can be deferred
  only with explicit acknowledgment
- `NICE-TO-HAVE` — optional improvement; safe to defer to a future iteration

Overall status:
- `approved` — no MUST-FIX items; any SHOULD-FIX items are documented
- `changes_requested` — MUST-FIX items or critical SHOULD-FIX items require action
- `blocked` — planning mistake or missing facts; developer cannot address without re-planning

## Template

```markdown
# Review — Iteration <N>

## Status
- Workspace: <workspace-id>
- Iteration: <N>
- Review status: blocked | changes_requested | approved
- Date: <ISO 8601 date>

## Executive summary
- MUST-FIX: <count> items
- SHOULD-FIX: <count> items
- NICE-TO-HAVE: <count> items
- Overall: <one sentence verdict>

## Scope alignment

### Delivered vs. intended
<Did the implementation address what iter-N-plan.md specified? Note any gaps.>

### Scope drift
<Any behavior implemented that was explicitly out of scope or not in the iteration plan.>

### Missing from intended scope
<Anything from the iteration plan that was not addressed.>

## Scenario evidence

For each source scenario from iter-N-plan.md:
- S1 — <title>: addressed | partial | missing — <brief note>
- S2 — <title>: addressed | partial | missing — <brief note>

## Engineering smell pass

### Redundant / dead / unreachable code
<Code that is duplicated, unreachable, or no longer used.>

### Superfluous complexity
<Abstractions, layers, or patterns that add complexity without corresponding benefit.>

### Performance footguns
<N+1 queries, unbounded loops, unnecessary allocations, or other performance risks.>

### Consistency and maintainability
<Naming inconsistencies, style drift, patterns that conflict with the surrounding codebase,
or structure that will be difficult to maintain.>

## Test quality

### Strengths
<What the tests do well.>

### Weaknesses
<Tests that are brittle, too narrow, test implementation rather than behavior, or are
missing for key scenarios.>

### Improvements
<Specific suggestions for making the tests more durable or comprehensive.>

## Risk hotspots

### Security
<Any security concerns: input validation, key handling, permission checks, injection risks.>

### Data / contracts
<Schema changes, migration risks, API contract changes, data invariant violations.>

### Performance / operability
<Anything that would degrade under load or make the system harder to operate.>

## Recommended next smallest step
<If changes_requested or blocked: the single most important thing the developer should do
next. One sentence. This is the starting point, not the full list.>

## Findings detail

For each finding (also recorded in iter-N-review.json via auggd tools review update):

### Finding <N> — <severity>
- File: `path/to/file.py`
- Description: <what the problem is>
- Suggestion: <concrete recommendation>

## Questions / clarifications
<Anything the reviewer is uncertain about or wants the developer to explain.>
```

## Writing guidance

**Executive summary**: write this last, after completing both passes. The counts should
match the findings in the JSON counterpart.

**Scope alignment**: this is Pass 1. Do not skip it even if the code looks correct. The
most common review failure is implementing the right code for the wrong behavior.

**Engineering smell pass**: this is Pass 2. Be specific. "This is messy" is not a finding.
"The `resolve_workspace` function duplicates logic from `manager.py:152` and should call
the existing helper" is a finding.

**Recommended next smallest step**: this is the most important line in the review. The
developer should be able to start with this step without re-reading the full review.
If the review is `approved`, this field can be a future improvement suggestion or omitted.

## Relationship to iter-N-review.json

The JSON counterpart is updated via `auggd tools review --ws=<N> update <N> --data`.
Each finding in the markdown should have a corresponding structured entry in the JSON.
The overall status set via `auggd tools review --ws=<N> done <N> <status>` must match
the narrative verdict in this document.
