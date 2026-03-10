# open-auggd — Phase 2 Specification

## Overview

Phase 2 is content authoring. The Python CLI, workspace management, tools layer, and TypeScript
wrappers are complete and untouched. Phase 2 fills in all placeholder content in
`src/open_auggd/templates/` — the 7 agent prompts, 8 command prompts, and 12 skill files that
were stubbed out in Phase 1.

When Phase 2 is complete, `auggd install` deploys a fully functional OpenCode workflow: agents
that understand their roles, commands that enforce the phase gate sequence, and skills that
provide reusable execution guidance and document templates.

---

## Scope

### In scope

- Write full content for all 7 `templates/agents/oag-*.md` files
- Write full content for all 8 `templates/commands/oag-*.md` files
- Write full content for all 12 `templates/skills/oag-*/SKILL.md` files

### Out of scope

- No new skills, agents, or commands beyond the 12/7/8 already in the install manifest
- No changes to Python CLI, tools layer, workspace models, or TypeScript wrappers
- No test additions (test gaps for `document.py` and `updater.py` deferred to Phase 3)
- No README update
- No changes to `pyproject.toml`, `install-manifest.json`, or file layout

---

## Authoring Rules

### Models

All templates use `model: opencode/gpt-5-nano`. This is the config-managed default — users
override per-agent or per-command via `auggd.toml` or `OAG_*` env vars, then run `auggd update`
to propagate changes into frontmatter. No agent or command hardcodes a different model.

### State access

Agents and commands interact with workspace state exclusively through the `auggd tools` CLI.
No agent body references raw artifact file paths for reading or writing. The tools layer owns
path resolution, JSON validation, and gate enforcement.

```
# Correct — agent instructs calls like:
auggd tools explore --ws=<N> status
auggd tools plan --ws=<N> iter create
auggd tools develop --ws=<N> done 3

# Incorrect — agents must NOT do:
cat .auggd/workspace/<id>/plan/iter-1-plan.json
```

Agents may read files for context (e.g., reading `plan/spec.md` to understand scope before
coding) but must use `auggd tools` for all state-mutating operations and for structured status
reads.

### Artifact paths

Phase 2 content must use the Phase 1 workspace artifact paths, not the reference paths:

| Reference path | Phase 1 / Phase 2 path |
|---|---|
| `workspace/<WS>/exploration.md` | `<WS>/explore/<topic>.md` |
| `workspace/<WS>/spec.md` | `<WS>/plan/spec.md` |
| `workspace/<WS>/iterations/iter-N.md` | `<WS>/plan/iter-N-plan.md` |
| `workspace/<WS>/devlog.md` | `<WS>/develop/iter-N-devlog.md` |
| `workspace/<WS>/reviews/iter-N-review.md` | `<WS>/review/iter-N-review.md` |
| `workspace/<WS>/contexts/working-set.md` | no equivalent — omit |
| `workspace/<WS>/contexts/iter-N-context.md` | no equivalent — omit |
| `workspace/<WS>/reviews/external-feedback.md` | no equivalent — omit |
| `workspace/<WS>/publish-log.md` | no equivalent — omit |
| `docs/metadata.json` | `.auggd/document-metadata.json` |

The `<WS>` token in agent and skill content refers to the full workspace directory path, which
is resolved by the `auggd tools` commands from `--ws=<N|slug>`. Agents receive the resolved
path from tool output.

### Permissions

All agent frontmatter includes granular bash allow-lists, task routing rules, and webfetch
permissions appropriate to each agent's role. The pattern follows the reference agents
(`opencode-setting-reference/agents/`). Read-only agents (explorer, planner, reviewer) deny
`edit` and restrict bash to read-only commands. The developer agent allows edit and a curated
bash set. The finalizer agent allows commits but requires confirmation for push.

### Command routing

Commands route directly to their corresponding subagent via `agent:` frontmatter — not through
`oag-auggd`. The `oag-status.md` and `oag-resume.md` commands route to `oag-auggd` because
they require cross-phase reasoning and delegation.

### No publish phase

The reference `publish` command and `publish-workflow` skill have no equivalent. The `finalize`
phase replaces publish: it marks the iteration complete and optionally commits. Push and PR are
manual user actions after finalize. `oag-finalize-workflow` is adapted from `publish-workflow`
with all PR/CI/push mechanics removed.

### Trunk-based workflow

The reference `trunk-based-workflow` skill has no `oag-*` equivalent and is not added. Where
git workflow guidance is needed (e.g., in `oag-finalizer.md`), a brief inline note is included
rather than loading a separate skill.

---

## Source Material

All content is adapted from `opencode-setting-reference/`. The mapping from reference files to
Phase 2 targets is documented per section below. "Adapted from" means: same structure, same
intent, updated paths, updated tool calls, removed publish/trunk/working-set references.

---

## Skills

Skills are authored first. Agents and commands reference them by name; having content in place
before writing agents prevents forward references to undefined material.

### Skill file format

```markdown
---
name: oag-<skill-name>
description: <one sentence>
compatibility: opencode
---

# <Title>

<content>
```

All skill names are prefixed `oag-`. The `compatibility: opencode` field is preserved from the
reference.

### Workflow and phase skills (8)

These provide phase execution guidance — what to do, what not to do, required outputs, and
handoff conditions. Each skill maps to a workflow phase.

#### `oag-exploration-workflow`

Adapted from: `exploration-workflow`

Content requirements:
- Phase: explore
- Primary artifacts: `<WS>/explore/<topic>.md` files + `<WS>/explore/attachments.json`
- Instructs calling `auggd tools explore --ws=<N> start` before writing, `done` when complete
- Covers: clarify problem, identify constraints, inspect repo, gather external info, surface
  plausible directions
- Required output in `<topic>.md`: problem statement, context, constraints, repo observations,
  external findings + sources, candidate approaches, open questions, recommended next move
- Required output via `auggd tools explore done`: `explore_status = done`
- Exit criteria: problem clearly stated, key unknowns answered or listed, at least one plausible
  direction exists
- Handoff: to plan when framing is good enough; back to explore if still too vague

Key changes from reference: no `working-set.md`, no branch creation instructions, calls
`auggd tools explore` instead of writing files directly.

#### `oag-planning-workflow`

Adapted from: `planning-workflow`

Content requirements:
- Phase: plan
- Primary artifacts: `<WS>/plan/spec.md`, `<WS>/plan/iter-N-plan.md`,
  `<WS>/plan/iter-N-plan.json`
- Instructs calling `auggd tools plan --ws=<N> start` before writing, `iter create` for new
  iterations, `iter done <N>` when acceptance criteria are complete
- Covers: decide next step (spec refinement | new iteration | revised iteration | more
  exploration); keep each iteration a single TDD-sized task; front-load riskiest uncertainty
- Required output in `iter-N-plan.md`: objective, scope, non-goals, touch points, test plan,
  quality gates, stop-and-ask triggers, definition of done
- Required output via `auggd tools plan iter done <N>`: non-empty `acceptance_criteria` in JSON
- Exit criteria: next step explicit, iteration small + testable, scope bounded, developer can
  begin without re-planning
- Handoff: to develop only when iteration is implementation-ready; otherwise back to explore

Key changes from reference: paths updated, `auggd tools plan` calls for all state mutations,
no `working-set.md` references, no `contexts/` references.

#### `oag-development-workflow`

Adapted from: `development-workflow`

Content requirements:
- Phase: develop
- Primary artifacts: `<WS>/develop/iter-N-devlog.md`, `<WS>/develop/iter-N-devlog.json`
- Instructs calling `auggd tools develop --ws=<N> start <N>` before coding, `update <N>` after
  each meaningful step, `done <N>` when cycle is complete
- Covers: strict RED → GREEN → REFACTOR; use plan and spec before broad repo exploration;
  small TDD slices; run quality gates; do not commit
- Required devlog output (written to `devlog.md`, status tracked in `devlog.json`): iteration,
  what changed, files touched, tests run + results, scenarios addressed, current assessment,
  next smallest RED step, open questions / blockers
- Exit criteria: behavior implemented, tests green, in scope, devlog current
- Handoff: to review when cycle is ready; if blocked, route back to plan or explore

Key changes from reference: no `working-set.md` or `contexts/` reads; all devlog state via
`auggd tools develop update/done`; no commit.

#### `oag-review-workflow`

Adapted from: `review-workflow`

Content requirements:
- Phase: review
- Primary artifacts: `<WS>/review/iter-N-review.md`, `<WS>/review/iter-N-review.json`
- Instructs calling `auggd tools review --ws=<N> start <N>` to create review artifacts,
  `update <N>` to record findings, `done <N> <status>` with final verdict
- Two required review passes:
  - Pass 1: intent alignment (satisfies scoped behavior? stayed in scope? tests aligned?)
  - Pass 2: engineering smell pass (dead code, superfluous complexity, perf footguns,
    maintainability drift, brittle tests, risk hotspots)
- Required categories: `MUST-FIX | SHOULD-FIX | NICE-TO-HAVE`
- Overall status: `blocked | changes_requested | approved`
- Required output: executive summary, scope alignment, scenario evidence, engineering smell
  findings, test quality notes, risk hotspots, next smallest corrective step, review status
- Exit criteria: status explicit, findings specific + actionable, next move clear
- Handoff: approved → finalize; changes needed → develop; planning mistake → plan;
  missing facts → explore

Key changes from reference: no `working-set.md` or `contexts/` reads; all status via
`auggd tools review`; no `pr-checklist` skill reference.

#### `oag-finalize-workflow`

Adapted from: `publish-workflow` (with publish/PR/CI mechanics removed)

Content requirements:
- Phase: finalize
- Primary artifact: `<WS>/plan/progress-log.json` (updated by `auggd tools finalize`)
- Instructs calling `auggd tools finalize --ws=<N> iter <N>` (with optional `--commit` flag)
- Covers: verify iteration review is `approved` (gate enforced by tool); update iteration
  state; optionally commit changes; record finalization in progress-log
- Does NOT cover: push, PR creation, CI, external feedback routing — these are manual user
  decisions after finalize
- Exit criteria: iteration marked `finalized` in progress-log, commit made if `--commit` was
  passed, workspace ready for next iteration or document phase
- Handoff: if more iterations remain → plan; if all iterations done → document

Key changes from reference: no push/PR/branch instructions; no `publish-log.md`; no
`external-feedback.md`; calls `auggd tools finalize` instead of git commands directly.

#### `oag-documentation-workflow`

Adapted from: `documentation-workflow`

Content requirements:
- Phase: document
- State artifact: `.auggd/document-metadata.json`
- Instructs calling `auggd tools document check` first (confirms git repo + compares HEAD hash
  to metadata), `init` if metadata absent, `update-metadata` after documentation is refreshed
- Covers: detect what changed since last doc generation; decide which areas need refresh;
  update only relevant docs; refresh metadata; keep docs practical; use Mermaid where it
  materially improves understanding
- Diataxis structure: Tutorial | How-to | Reference | Explanation
- Exit criteria: affected docs updated, metadata refreshed, known gaps recorded
- Handoff: usually ends the loop; missing facts → explore; planning drift → plan

Key changes from reference: metadata path is `.auggd/document-metadata.json` not
`docs/metadata.json`; state managed via `auggd tools document`; project-scoped (not
workspace-scoped).

#### `oag-tdd-standards`

Adapted from: `tdd-playbook`

Content requirements: near-verbatim from reference. The `tdd-playbook` is already general and
not path-specific. Changes:
- Remove reference to `trunk-based-workflow` in scope discipline section
- Replace any `workspace/<WS>/` path mentions with the Phase 1 equivalents
- Update iteration definition to match Phase 1: "one TDD-sized behavior slice" that produces
  `iter-N-plan.md` + `iter-N-devlog.md`

#### `oag-documentation-standards`

Adapted from: `documentation-standards`

Content requirements: near-verbatim from reference. Changes:
- Replace `docs/metadata.json` with `.auggd/document-metadata.json`
- Update the metadata JSON shape to match the Phase 1 `DocumentMetadata` schema:
  `last_commit_hash`, `last_commit_summary`, `generated_at`, `documents_updated`, `known_gaps`

---

### Template skills (4)

These define the markdown document structure that agents write into workspace artifact files.
They are loaded by agents before producing narrative output.

#### `oag-devlog-template`

Adapted from: `devlog-template`

Artifact: `<WS>/develop/iter-N-devlog.md` (narrative companion to `iter-N-devlog.json`)

Template sections:
```
# Devlog — iter-<N> — <short title>

## Status
- Workspace: <workspace-id>
- Iteration: <N>
- Status: in_progress | dev_complete

## Entry — <ISO 8601 timestamp>
### Goal for this session
### What changed
### Files touched
### Tests run
- command: <command>
  result: <pass/fail/output summary>
### Other checks (lint / build / typecheck)
### Scenarios addressed
- [ ] <scenario from acceptance criteria>
### Current assessment
### Next smallest RED step
### Open questions / blockers
```

Usage note: `iter-N-devlog.md` is append-only by default; new entries are added below existing
ones. The JSON counterpart (`iter-N-devlog.json`) is updated via `auggd tools develop update`.

#### `oag-spec-template`

Adapted from: `spec-template`

Artifact: `<WS>/plan/spec.md`

Template sections:
```
# Spec — <Feature / Work Item Name>

## Status
- Workspace: <workspace-id>
- Owner: <agent or user>
- Updated: <ISO 8601 date>
- Status: draft | active | partial | stable

## Problem
<one short paragraph>

## Goals
- [ ] <goal 1>
- [ ] <goal 2>

## Non-goals

## Users / actors

## Core scenarios
Use scenario IDs (S1, S2, ...) for cross-referencing in iterations and reviews.

### S1 — <title>
- Given: ...
- When: ...
- Then: ...

## Constraints and invariants

## Out of scope

## Open questions

## Notes
```

#### `oag-iteration-template`

Adapted from: `iteration-template`

Artifact: `<WS>/plan/iter-N-plan.md` (narrative companion to `iter-N-plan.json`)

Rules: one clear behavior slice, small enough for one RED → GREEN → REFACTOR loop, explicit
stop conditions, reviewable as a unit.

Template sections:
```
# Iteration <N> — <Short Title>

## Status
- Workspace: <workspace-id>
- Iteration: <N>
- Status: pending | in_progress | dev_complete | review_complete | finalized

## Objective
<one sentence>

## Source scenarios
- [ ] S1 — <title>
- [ ] S2 — <title>

## In scope

## Out of scope

## Touch points
Expected files / modules / surfaces that will change.

## Test plan
Tests to add or update.

## Quality gates
- [ ] Tests green
- [ ] Lint passes
- [ ] Build / typecheck passes

## Stop and ask if
- <trigger 1>
- <trigger 2>

## Definition of done
- [ ] Behavior implemented
- [ ] Tests green
- [ ] No unapproved scope expansion
- [ ] Ready for review

## Notes
```

Usage note: `iter-N-plan.md` is the narrative document. Structured metadata lives in
`iter-N-plan.json` and is managed via `auggd tools plan`. The `acceptance_criteria` field in
the JSON must be non-empty before `auggd tools plan iter done <N>` succeeds.

#### `oag-review-template`

Adapted from: `review-template`

Artifact: `<WS>/review/iter-N-review.md` (narrative companion to `iter-N-review.json`)

Required labels: `MUST-FIX | SHOULD-FIX | NICE-TO-HAVE`
Overall status: `blocked | changes_requested | approved`

Template sections:
```
# Review — Iteration <N>

## Status
- Workspace: <workspace-id>
- Iteration: <N>
- Review status: blocked | changes_requested | approved
- Date: <ISO 8601 date>

## Executive summary
- MUST-FIX: <count>
- SHOULD-FIX: <count>
- NICE-TO-HAVE: <count>

## Scope alignment
- In scope: <what was delivered vs. what was planned>
- Drift: <any scope creep>
- Missing: <anything from the iteration plan not delivered>

## Scenario evidence
- S1 — <title>: addressed / partial / missing
- S2 — <title>: addressed / partial / missing

## Engineering smell pass

### Redundant / dead / unreachable

### Superfluous complexity

### Performance footguns

### Consistency / maintainability

## Test quality
- Strengths:
- Weaknesses:
- Improvements:

## Risk hotspots
- Security:
- Data / contracts:
- Performance / operability:

## Recommended next smallest step

## Questions / clarifications
```

---

## Agents

Agents are authored after skills. Each agent loads relevant skills by name.

### Agent file format

```markdown
---
name: oag-<name>
description: <one sentence role description>
mode: primary | subagent
model: opencode/gpt-5-nano
temperature: <value>
steps: <value>
tools:
  write: true | false
  edit: true | false
  bash: true
permission:
  edit: allow | ask | deny
  bash:
    "*": deny | ask
    "ls*": allow
    # ... per-command allow-list
  webfetch: allow | deny
  task:
    "*": deny
    "oag-<name>": allow
    # ...
hidden: true | false
---

You are **<AgentName>**.

## Ownership
...

## What you must read first
...

## Skills to load
...

## Decision rules
...

## What you must never do
...

## Style
...
```

The `hidden: true` field suppresses the agent from `@` autocomplete in OpenCode. All subagents
are hidden. `oag-auggd` is not hidden.

### Agent specifications

#### `oag-auggd.md`

Adapted from: `manager.md`

Frontmatter:
- `mode: primary`
- `hidden: false` (the only non-hidden agent)
- `tools.write: true`, `tools.edit: true`
- `permission.edit: ask`
- Bash allow-list: read-only repo commands (`ls`, `cat`, `git status/log/diff`) + `auggd ws *`
  and `auggd tools * status` calls; deny write bash by default
- Task routing: allow all 6 oag-* subagents; deny everything else
- `webfetch: allow`

Body sections:
- **Ownership**: traffic controller and orchestrator; delegates to subagents based on user
  intent; relays outcomes back without deep involvement in execution; does not implement,
  design, or write documentation directly
- **Routing logic**: map user requests to phases:
  - "explore / research / investigate" → `@oag-explorer`
  - "plan / design / iteration" → `@oag-planner`
  - "develop / implement / code" → `@oag-developer`
  - "review / check / audit" → `@oag-reviewer`
  - "finalize / close out / commit" → `@oag-finalizer`
  - "document / docs / readme" → `@oag-documenter`
  - "status / where are we" → read `auggd ws info <N>` and summarize
- **Workspace resolution**: always confirm `--ws=<N>` before routing; if ambiguous, ask user
- **What to read first**: `auggd ws list` to orient; `auggd ws info <N>` for current phase;
  subagent output for detailed state
- **Skills to load**: none (routing-only agent)
- **What you must never do**: implement code, write specs or plans, perform reviews, make
  commits, replace subagents as the executor; silently widen scope; pretend to have done work
  delegated to a subagent

#### `oag-explorer.md`

Adapted from: `researcher.md` (primary) + ideation sections of `architect.md`

Frontmatter:
- `mode: subagent`
- `hidden: true`
- `tools.write: true` (writes exploration narrative files), `tools.edit: true`
- `permission.edit: allow`
- Bash allow-list: read-only (`ls`, `cat`, `rg`, `grep`, `find`, `git status/diff/log/show`,
  `auggd tools explore *`, `auggd ws info *`)
- Task routing: deny all (researcher role — no sub-delegation)
- `webfetch: allow`

Body sections:
- **Ownership**: fact-gathering, ideation, external research, repo reconnaissance; can be
  re-entered at any phase for consulting on ideas or reviewing outcomes
- **What you must do first**: call `auggd tools explore --ws=<N> start` to initialize; then
  `auggd tools explore --ws=<N> status` to check current state
- **Execution steps**:
  1. Clarify problem and identify constraints
  2. Inspect repo (relevant paths, patterns, commands, boundaries)
  3. Gather external information when libraries/tooling/freshness matters
  4. Surface 2–5 plausible directions when multiple solutions exist
  5. Write narrative to `<WS>/explore/<topic>.md` using `oag-exploration-workflow`
  6. Call `auggd tools explore --ws=<N> done` when exploration is complete
- **Skills to load**: `oag-exploration-workflow`
- **What you must never do**: write code, create specs, make commits; treat uncertainty as
  resolved; skip the `auggd tools explore` calls

#### `oag-planner.md`

Adapted from: `architect.md` (planning focus only)

Frontmatter:
- `mode: subagent`
- `hidden: true`
- `tools.write: true`, `tools.edit: true`
- `permission.edit: allow`
- Bash allow-list: read-only + `auggd tools plan *`, `auggd tools explore --ws=<N> status`,
  `auggd ws info *`
- Task routing: allow `oag-explorer` (to get fresh facts); deny everything else
- `webfetch: deny` (call oag-explorer for external facts)

Body sections:
- **Ownership**: solution strategy, iteration shaping, spec authorship; each iteration must be
  a single TDD-sized task — no batching
- **What you must read first**:
  1. `auggd tools explore --ws=<N> status` (confirm explore is done)
  2. `<WS>/explore/<topic>.md` files (exploration narratives)
  3. `<WS>/plan/spec.md` if it exists (current spec)
  4. Existing `iter-N-plan.json` files via `auggd tools plan --ws=<N> iter status <N>`
  5. `<WS>/review/iter-N-review.md` for latest review findings if iterating
- **Execution steps**:
  1. Call `auggd tools plan --ws=<N> start` (requires explore done)
  2. Write or update `<WS>/plan/spec.md` using `oag-spec-template`
  3. Call `auggd tools plan --ws=<N> iter create` for each new iteration
  4. Write `<WS>/plan/iter-N-plan.md` using `oag-iteration-template`
  5. Call `auggd tools plan --ws=<N> iter done <N>` when acceptance criteria are written
- **Skills to load**: `oag-planning-workflow`, `oag-spec-template`, `oag-iteration-template`,
  `oag-tdd-standards`
- **What you must never do**: batch multiple behaviors into one iteration; create iterations
  without acceptance criteria; skip the gate checks; implement code

#### `oag-developer.md`

Adapted from: `developer.md`

Frontmatter:
- `mode: subagent`
- `hidden: true`
- `tools.write: true`, `tools.edit: true`
- `permission.edit: allow`
- Bash allow-list (same granularity as reference developer):
  - Read-only: `ls`, `cat`, `rg`, `grep`, `find`, `git status/diff/log/show/branch`
  - Safe write: `git switch`, `git checkout`, `git fetch`, `git pull`, `git add`, `git restore`
  - Test/quality: `pytest*`, `python -m pytest*`, `npm test*`, `pnpm test*`, `yarn test*`,
    `go test*`, `cargo test*`, `make test*`, `make lint*`, `ruff*`, `eslint*`, `pre-commit*`
  - Tool calls: `auggd tools develop *`, `auggd ws info *`
  - Ask: `git commit*`, `git push*`, `git merge*`, `git rebase*`, `git reset*`, `git clean*`
- Task routing: allow `oag-explorer` (for repo spelunking when lost); deny everything else
- `webfetch: deny`

Body sections:
- **Ownership**: TDD implementation of exactly one planned iteration at a time; does not commit
- **What you must read first**:
  1. `auggd tools develop --ws=<N> status <N>` (current devlog state)
  2. `<WS>/plan/iter-N-plan.md` (what to build)
  3. `<WS>/plan/spec.md` (overall intent and constraints)
  4. `<WS>/review/iter-N-review.md` if re-entering after review changes
  5. `<WS>/develop/iter-N-devlog.md` tail if resuming
- **Execution steps**:
  1. Call `auggd tools develop --ws=<N> start <N>` to initialize devlog
  2. Work in RED → GREEN → REFACTOR slices
  3. Call `auggd tools develop --ws=<N> update <N> --data '<json>'` after each meaningful step
  4. Run quality gates (tests, lint, typecheck)
  5. Append narrative entry to `iter-N-devlog.md` using `oag-devlog-template`
  6. Call `auggd tools develop --ws=<N> done <N>` when cycle is complete; do not commit
- **Skills to load**: `oag-development-workflow`, `oag-devlog-template`, `oag-tdd-standards`
- **What you must never do**: widen scope; invent new architecture; make commits; skip devlog
  updates; start a new iteration without calling `auggd tools develop start`

#### `oag-reviewer.md`

Adapted from: `reviewer.md`

Frontmatter:
- `mode: subagent`
- `hidden: true`
- `tools.write: false`, `tools.edit: false`
- `permission.edit: deny`
- Bash allow-list: read-only only (`ls`, `cat`, `rg`, `grep`, `find`, `git diff/log/show`,
  `auggd tools review *`, `auggd tools develop --ws=<N> status *`, `auggd ws info *`)
- Task routing: deny all
- `webfetch: deny`

Body sections:
- **Ownership**: intent alignment + engineering smell detection for exactly one iteration;
  produces structured findings with severity labels; does not implement fixes
- **What you must read first**:
  1. `auggd tools review --ws=<N> status <N>` (if review already started)
  2. `<WS>/plan/iter-N-plan.md` (what was intended)
  3. `<WS>/plan/spec.md` (overall intent)
  4. `<WS>/develop/iter-N-devlog.md` (what was done)
  5. `auggd tools develop --ws=<N> status <N>` (confirm `dev_complete`)
  6. Relevant changed files via git diff
- **Execution steps**:
  1. Call `auggd tools review --ws=<N> start <N>` (requires `dev_complete`)
  2. Perform Pass 1: intent alignment
  3. Perform Pass 2: engineering smell pass
  4. Write `<WS>/review/iter-N-review.md` using `oag-review-template`
  5. Call `auggd tools review --ws=<N> update <N> --data '<json>'` for each finding
  6. Call `auggd tools review --ws=<N> done <N> <status>` with final verdict
- **Skills to load**: `oag-review-workflow`, `oag-review-template`
- **What you must never do**: implement fixes; approve when MUST-FIX items exist; write to any
  artifact other than the review files; skip the two-pass structure

#### `oag-finalizer.md`

Adapted from: `manager.md` (publish section only), with publish mechanics replaced by finalize

Frontmatter:
- `mode: subagent`
- `hidden: true`
- `tools.write: false`, `tools.edit: false`
- `permission.edit: deny`
- Bash allow-list: `auggd tools finalize *`, `auggd tools review --ws=<N> status *`,
  `auggd ws info *`, `git log*`, `git status*`; deny everything else
- Task routing: deny all
- `webfetch: deny`

Body sections:
- **Ownership**: iteration close-out once review is approved; marks iteration as finalized;
  optionally commits; does not push, open PRs, or do work beyond closing the iteration
- **What you must read first**:
  1. `auggd tools review --ws=<N> status <N>` (confirm `approved`)
  2. `auggd ws info <N>` (overall workspace state)
- **Execution steps**:
  1. Confirm review status is `approved` (tool enforces this, but confirm before calling)
  2. Call `auggd tools finalize --ws=<N> iter <N>` (optionally `--commit`)
  3. Confirm `progress-log.json` updated correctly
  4. Report finalization summary to `oag-auggd`
- **Skills to load**: `oag-finalize-workflow`
- **What you must never do**: finalize an iteration with `changes_requested` or `blocked`
  review status; push or open PRs; make code changes; modify workspace artifacts beyond what
  the finalize tool does

#### `oag-documenter.md`

Adapted from: `documenter.md`

Frontmatter:
- `mode: subagent`
- `hidden: true`
- `tools.write: true`, `tools.edit: true`
- `permission.edit: ask`
- Bash allow-list: `ls`, `cat`, `rg`, `grep`, `find`, `git log*`, `git diff*`, `git show*`,
  `git rev-parse*`, `auggd tools document *`; deny everything else
- Task routing: allow `oag-explorer` (for fact-gathering if unclear); deny everything else
- `webfetch: allow`

Body sections:
- **Ownership**: project-wide documentation under `docs/`; not workspace-scoped; follows
  Diataxis (Tutorial / How-to / Reference / Explanation); tracks generation state in
  `.auggd/document-metadata.json`
- **What you must do first**:
  1. Call `auggd tools document check` (verifies git repo + returns hash + metadata state)
  2. If metadata absent, call `auggd tools document init`
- **Execution steps**:
  1. Detect what changed since last generation (compare `last_commit_hash` to HEAD)
  2. Decide which docs areas need refresh
  3. Update only relevant files under `docs/`
  4. Call `auggd tools document update-metadata --data '<json>'` with new hash + summary
- **Skills to load**: `oag-documentation-workflow`, `oag-documentation-standards`
- **What you must never do**: modify `.auggd/` directly (use `auggd tools document`); generate
  docs if project is not a git repo (tool will warn); invent structure that doesn't reflect the
  actual codebase

---

## Commands

Commands are authored last. Each command has frontmatter and a body describing workspace
context, inputs, and a `Do:` step list. Commands use `auggd tools` for state access — no shell
`!` inline file injection.

### Command file format

```markdown
---
name: oag-<name>
description: <one sentence>
agent: oag-<subagent>
[subtask: true]
model: opencode/gpt-5-nano
---

Workspace: `$1`
[Iteration: `$2`]

Do:
1) ...
2) ...
```

The `subtask: true` field indicates the command creates a focused subtask delegated directly to
the named agent. Commands that need cross-phase routing (`oag-status`, `oag-resume`) omit
`subtask` and route to `oag-auggd`.

### Command specifications

#### `oag-explore.md`

- `agent: oag-explorer`
- `subtask: true`

Parameters: `$1` = workspace reference (number or slug)

Do steps:
1. Load skills: `oag-exploration-workflow`
2. Run `auggd tools explore --ws=$1 status` to check current state
3. If not started, run `auggd tools explore --ws=$1 start` to initialize
4. Clarify the exploration topic with the user if not already provided
5. Gather repo facts: structure, relevant paths, patterns, existing tests and commands
6. Gather external facts if libraries, APIs, or external tooling are involved
7. Write exploration narrative to `<WS>/explore/<topic>.md`
8. When exploration is complete, run `auggd tools explore --ws=$1 done`
9. Summarize findings and recommended next move

#### `oag-plan.md`

- `agent: oag-planner`
- `subtask: true`

Parameters: `$1` = workspace reference

Do steps:
1. Load skills: `oag-planning-workflow`, `oag-spec-template`, `oag-iteration-template`,
   `oag-tdd-standards`
2. Run `auggd tools explore --ws=$1 status` to confirm explore is done
3. Run `auggd ws info $1` to check current plan state
4. Read `<WS>/explore/<topic>.md` files for context
5. Decide next step: write/update spec | create new iteration | revise existing iteration |
   route back to explore
6. Write or update `<WS>/plan/spec.md` if spec needs changes
7. If creating an iteration: run `auggd tools plan --ws=$1 iter create`, write
   `<WS>/plan/iter-N-plan.md`, populate acceptance criteria
8. Run `auggd tools plan --ws=$1 iter done <N>` once acceptance criteria are complete
9. Summarize what was planned and recommended next move

#### `oag-develop.md`

- `agent: oag-developer`
- `subtask: true`

Parameters: `$1` = workspace reference, `$2` = iteration number

Do steps:
1. Load skills: `oag-development-workflow`, `oag-devlog-template`, `oag-tdd-standards`
2. Run `auggd tools develop --ws=$1 status $2` to check current devlog state
3. Read `<WS>/plan/iter-$2-plan.md` for what to implement
4. Read `<WS>/plan/spec.md` for overall intent and constraints
5. If resuming: read `<WS>/develop/iter-$2-devlog.md` tail for context
6. If review changes are required: read `<WS>/review/iter-$2-review.md` for findings
7. If not started: run `auggd tools develop --ws=$1 start $2`
8. Implement using strict RED → GREEN → REFACTOR
9. Update devlog via `auggd tools develop --ws=$1 update $2 --data '<json>'` at each step
10. Append narrative entry to `<WS>/develop/iter-$2-devlog.md`
11. Run quality gates (tests, lint, typecheck)
12. Run `auggd tools develop --ws=$1 done $2` when complete; do not commit

#### `oag-review.md`

- `agent: oag-reviewer`
- `subtask: true`

Parameters: `$1` = workspace reference, `$2` = iteration number

Do steps:
1. Load skills: `oag-review-workflow`, `oag-review-template`
2. Run `auggd tools develop --ws=$1 status $2` to confirm `dev_complete`
3. Read `<WS>/plan/iter-$2-plan.md` and `<WS>/plan/spec.md`
4. Read `<WS>/develop/iter-$2-devlog.md`
5. Inspect changed files (git diff)
6. Run `auggd tools review --ws=$1 start $2`
7. Perform Pass 1: intent alignment
8. Perform Pass 2: engineering smell pass
9. Write `<WS>/review/iter-$2-review.md`
10. Run `auggd tools review --ws=$1 update $2 --data '<json>'` for each finding
11. Run `auggd tools review --ws=$1 done $2 <status>`
12. Summarize verdict and next recommended step

#### `oag-finalize.md`

- `agent: oag-finalizer`
- `subtask: true`

Parameters: `$1` = workspace reference, `$2` = iteration number

Do steps:
1. Load skills: `oag-finalize-workflow`
2. Run `auggd tools review --ws=$1 status $2` — confirm `approved`; stop if not approved
3. Run `auggd tools finalize --ws=$1 iter $2` (add `--commit` if user requested a commit)
4. Confirm finalization in progress-log via `auggd ws info $1`
5. Report: iteration finalized, commit hash if committed, next recommended action

#### `oag-document.md`

- `agent: oag-documenter`
- `subtask: true`

Parameters: none (project-scoped, no workspace reference)

Do steps:
1. Load skills: `oag-documentation-workflow`, `oag-documentation-standards`
2. Run `auggd tools document check` — confirm git repo, get HEAD hash and metadata state
3. If metadata absent: run `auggd tools document init`
4. Determine what changed since last generation (`last_commit_hash` vs HEAD)
5. Identify which docs areas need refresh
6. Update relevant files under `docs/` following Diataxis structure
7. Run `auggd tools document update-metadata --data '<json>'` with new hash and summary
8. Report what was updated and any known gaps recorded

#### `oag-status.md`

- `agent: oag-auggd`
- (no `subtask`)

Parameters: `$1` = workspace reference

Do steps:
1. Run `auggd ws info $1` for high-level workspace state
2. Run `auggd tools explore --ws=$1 status`
3. Run `auggd tools plan --ws=$1 iter status <N>` for each known iteration
4. Determine current phase from artifact states
5. Identify: missing artifacts, stale state, whether blocked or ready
6. Output concise status: current phase, key artifacts present/missing, biggest blocker, next
   recommended command
7. Do not modify any files

#### `oag-resume.md`

- `agent: oag-auggd`
- (no `subtask`)

Parameters: `$1` = workspace reference, `$2` = iteration hint (optional)

Do steps:
1. Run `auggd ws info $1`
2. Run `auggd tools explore --ws=$1 status`
3. If iterations exist: run `auggd tools plan --ws=$1 iter status <N>` for each
4. If $2 provided: run `auggd tools develop --ws=$1 status $2` and
   `auggd tools review --ws=$1 status $2` if relevant
5. Read the current phase from artifact states (same logic as `oag-status`)
6. If obvious and safe, route directly to the appropriate phase command
7. If ambiguous, output a concise decision summary and list what is missing or stale
8. Prefer the smallest viable next move

---

## Build Order

1. **Skills — workflow/standard** (8 files)
   - `oag-exploration-workflow`
   - `oag-planning-workflow`
   - `oag-development-workflow`
   - `oag-review-workflow`
   - `oag-finalize-workflow`
   - `oag-documentation-workflow`
   - `oag-tdd-standards`
   - `oag-documentation-standards`

2. **Skills — templates** (4 files)
   - `oag-devlog-template`
   - `oag-spec-template`
   - `oag-iteration-template`
   - `oag-review-template`

3. **Agents — subagents** (6 files)
   - `oag-explorer`
   - `oag-planner`
   - `oag-developer`
   - `oag-reviewer`
   - `oag-finalizer`
   - `oag-documenter`

4. **Agents — primary** (1 file)
   - `oag-auggd`

5. **Commands** (8 files)
   - `oag-explore`
   - `oag-plan`
   - `oag-develop`
   - `oag-review`
   - `oag-finalize`
   - `oag-document`
   - `oag-status`
   - `oag-resume`

---

## Acceptance Criteria

- [ ] All 12 `SKILL.md` files contain substantive content — no `<!-- Phase 2: -->` placeholders
- [ ] All 7 agent `.md` files contain full YAML frontmatter and complete body — no placeholders
- [ ] All 8 command `.md` files contain full frontmatter and `Do:` steps — no placeholders
- [ ] All agent prompts reference only Phase 1 artifact paths
- [ ] All agents and commands use `auggd tools` for state access — no direct artifact reads for
  state mutation
- [ ] All command `agent:` frontmatter names use `oag-*` prefixed agent names
- [ ] No agent or skill references workspace paths from the reference (`workspace/<WS>/...`)
- [ ] No agent references removed concepts: `working-set.md`, `publish-log.md`,
  `external-feedback.md`, `contexts/`, trunk-based workflow
- [ ] `auggd install` deploys all new content without errors
- [ ] `auggd reset` restores all new content correctly
- [ ] Existing 82 tests pass without modification (`make test` green)

---

## Out of Scope for Phase 2

- Missing tests for `document.py` tools and `updater.py` (deferred to Phase 3)
- README content (deferred to Phase 3)
- `pyproject.toml` description (deferred to Phase 3)
- Changes to install manifest or file layout
- Additional skills beyond the 12 existing stubs
- Any Python CLI or TypeScript tooling changes
