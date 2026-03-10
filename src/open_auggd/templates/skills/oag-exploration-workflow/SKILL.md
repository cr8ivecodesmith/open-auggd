---
name: oag-exploration-workflow
description: Phase skill for exploration work: clarify the problem, gather repo and external facts, and produce exploration artifacts under the workspace explore/ directory.
compatibility: opencode
---

# Exploration Workflow

Phase: explore
Primary artifacts: `<WS>/explore/<topic>.md` files, `<WS>/explore/attachments.json`

## What to do

1. Call `auggd tools explore --ws=<N> start` before writing any artifacts. This creates the
   `explore/` directory and initializes `attachments.json` if absent. Idempotent — safe to
   call when resuming.

2. Call `auggd tools explore --ws=<N> status` to check current state before continuing a
   prior session.

3. Clarify the problem in plain language. Separate what is known from what is assumed.
   If the request is vague, ask one clarifying question before exploring widely.

4. Identify known constraints and assumptions: technical, product, operational, time/scope,
   compatibility, security.

5. Inspect the repo for relevant surfaces: paths, entry points, existing patterns, test and
   build commands, boundaries. Do not over-explore — map what matters for this topic.

6. Gather external information when libraries, tools, APIs, or freshness of facts matter.
   Cite sources in the narrative.

7. Surface 2–5 plausible directions when multiple solutions exist. Evaluate each honestly.
   Do not converge prematurely on the most familiar option.

8. Write the exploration narrative to `<WS>/explore/<topic>.md`. Use one file per distinct
   topic; topic names correspond to entries in the `topics` list in `attachments.json`.

9. Call `auggd tools explore --ws=<N> done` when exploration is sufficiently complete to
   support planning. This sets `explore_status = done`.

## Required output in `<topic>.md`

```
# Exploration — <topic title>

## Problem
<plain language, one paragraph>

## Why this matters

## Context

## Constraints
- Technical:
- Product / UX:
- Time / scope:
- Compatibility / migration:
- Security / compliance:

## Repo findings
### Relevant paths
### Existing patterns to reuse
### Patterns / pitfalls to avoid
### Key commands (run / test / lint / build)

## External findings
### Sources
### Notes

## Candidate approaches
### Option A — <name>
- Summary:
- Pros:
- Cons:
- Risks:
- Fit:

### Option B — <name>
...

## Recommendation

## Open questions

## Suggested next move
continue exploring | move to planning | request missing info
```

## What NOT to do

- Do not write code or create specs during exploration.
- Do not call `done` until the problem is clearly stated and at least one plausible direction
  exists.
- Do not skip the repo inspection — plan quality depends on exploration quality.
- Do not treat candidate approaches as decisions; they are options until planning commits.
- Do not batch multiple unrelated topics into one exploration file.

## Exit criteria

- Problem clearly stated
- Key unknowns answered or explicitly listed with a plan to resolve them
- Relevant repo surfaces identified
- At least one plausible direction exists
- `explore_status = done` set via `auggd tools explore --ws=<N> done`

## Handoff

To `oag-plan` when facts and framing are good enough to support a TDD-sized iteration.
Back to `oag-explore` if still too vague — list what is missing and why it blocks planning.
