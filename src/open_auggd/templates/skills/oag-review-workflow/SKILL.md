---
name: oag-review-workflow
description: Phase skill for review work: judge the current TDD cycle against intent, smell-test the implementation, and produce a review artifact with actionable findings.
compatibility: opencode
---

# Review Workflow

Phase: review
Primary artifacts: `<WS>/review/iter-N-review.md`, `<WS>/review/iter-N-review.json`

## What to do

1. Call `auggd tools develop --ws=<N> status <N>` to confirm `dev_complete` before
   starting. Review requires development to be finished.

2. Call `auggd tools review --ws=<N> status <N>` if resuming a prior review session.

3. Read in this order:
   - `<WS>/plan/iter-N-plan.md` — what was intended
   - `<WS>/plan/spec.md` — overall intent and non-goals
   - `<WS>/develop/iter-N-devlog.md` — what was done and why
   - Changed files (via git diff or direct read)

4. Call `auggd tools review --ws=<N> start <N>` to initialize review artifacts.
   Requires `dev_complete`.

5. Perform **Pass 1 — Intent alignment**:
   - Does the implementation satisfy the scoped behavior from `iter-N-plan.md`?
   - Did it stay in scope? Check non-goals.
   - Are the tests aligned with the acceptance criteria?
   - Is anything from the iteration plan missing?

6. Perform **Pass 2 — Engineering smell pass**:
   - Redundant, dead, or unreachable code
   - Superfluous complexity or abstraction tax
   - Performance footguns (N+1 queries, unbounded loops, unnecessary allocations)
   - Consistency and maintainability drift
   - Brittle or low-value tests (testing implementation not behavior)
   - Risk hotspots: security, data/migration/contracts, operability

7. Write `<WS>/review/iter-N-review.md` using `oag-review-template`.

8. For each finding, call:
   `auggd tools review --ws=<N> update <N> --data '<json>'`

   ```json
   {
     "findings": [
       {
         "severity": "MUST-FIX",
         "file": "src/foo.py",
         "description": "...",
         "suggestion": "..."
       }
     ]
   }
   ```

   Severity levels:
   - `MUST-FIX` — blocks approval; correctness, security, or significant quality issue
   - `SHOULD-FIX` — strong recommendation; maintainability or risk concern
   - `NICE-TO-HAVE` — optional improvement; can be deferred

9. Call `auggd tools review --ws=<N> done <N> <status>` with one of:
   - `approved` — no MUST-FIX items; SHOULD-FIX items documented but not blocking
   - `changes_requested` — MUST-FIX or critical SHOULD-FIX items require developer action
   - `blocked` — planning mistake, missing facts, or cannot proceed without re-scoping

## Review quality bar

A good review:
- Is specific — each finding names a file and line range where relevant
- Is actionable — each finding includes a concrete suggestion, not just a complaint
- Distinguishes intent failures from implementation choices
- Does not invent new requirements that weren't in the iteration plan
- Identifies the **next smallest corrective step** when changes are requested

A finding that says "this could be better" with no suggestion is not a finding.

## What NOT to do

- Do not implement fixes — record findings and let the developer act on them.
- Do not approve when MUST-FIX items exist.
- Do not write to any artifact except the review files.
- Do not skip Pass 1 or Pass 2 — both are always required.
- Do not mark `blocked` for implementation-level issues — `changes_requested` is correct
  unless the iteration plan itself is wrong.

## Exit criteria

- Both passes complete
- All findings recorded in `iter-N-review.json` via `update`
- `iter-N-review.md` written with executive summary and next step
- Final status set via `auggd tools review --ws=<N> done <N> <status>`

## Handoff

`approved` → to `oag-finalize`
`changes_requested` → back to `oag-develop` with specific findings
`blocked` → back to `oag-plan` (planning mistake) or `oag-explore` (missing facts)
