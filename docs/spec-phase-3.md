# open-auggd — Phase 3 Specification

## Overview

Phase 3 is a clean rewrite. Phases 1 and 2 produced a working system and, more importantly,
produced the learning that now informs a better design. The existing code is treated as
exploration output — valuable as reference, not as a constraint.

The core design shifts from Phase 1/2 are:

1. **Unified artifact schema** — phase-scoped JSON files replaced by a single
   `iteration-log.json` and `workspace-metadata.json` per workspace.
2. **Model + tactics skill architecture** — monolithic workflow skills split into a principles
   layer (model) and a decision-making layer (tactics) per phase.
3. **First-class phase gates** — `approve`, `redirect`, and `interrupt` are explicit
   CLI actions, not inferred from artifact state.
4. **Context priming contract** — `auggd ws info <N>` is the defined entry point for every
   subagent call. Its output schema is the context package.
5. **Tool-enforced artifact validation** — the tools layer owns template validation.
   Skills define principles and tactics, not schema enforcement.

---

## Workflow

```
explore → plan → develop → review
  ↑_________________________↓  (tight loop)

finalize  (once review approved — iteration close-out)
document  (project-scoped — independent of workspace lifecycle)
```

Each phase produces artifacts. Each loop enforces the next. The pathway is malleable —
any phase can redirect to any other phase. The loop converges toward a finalized iteration.

---

## Workspace Structure

```
.auggd/                              # gitignored
  auggd.toml                         # project config
  install-manifest.json              # tracks all files written by auggd install
  workspace/                         # workspace root
    <uuid7base64>-<slug>/            # one dir per work item
      workspace-metadata.json        # workspace identity + current state
      iteration-log.json             # full phase history keyed by iteration
      files-manifest.json            # file activity tracking keyed by iteration
      spec.md                        # living specification
      attachments/                   # exploration outputs
        <topic>.md
        <screenshot>.<jpg|png>
      tmp/                           # agent scratch space, not tracked
  document-metadata.json             # document phase state (created on first document init)

.opencode/                           # committed to git
  agents/
  commands/
  skills/
  tools/
```

The workspace directory name is `<uuid7base64>-<slug>`. The UUID7 portion and slug are
stored separately in `workspace-metadata.json` for clean programmatic access.

---

## Artifact Schemas

### `workspace-metadata.json`

Identity and current state. Written by `auggd ws create`. Updated by phase gate actions.

```json
{
  "id": "AZXyo7HEfomfPS0bTF1uf",
  "slug": "add-user-authentication",
  "created_at": "2026-03-11T00:00:00Z",
  "updated_at": "2026-03-11T00:00:00Z",
  "current_phase": "develop",
  "current_iteration": 1,
  "title": "",
  "description": "",
  "scope": [],
  "non_goals": []
}
```

`current_phase` values: `explore | plan | develop | review | finalize | done`

### `iteration-log.json`

Single source of truth for all phase activity. Keyed by iteration number. Iteration `0`
is reserved for workspace-level explore/plan activity before any implementation iteration
begins. Iterations `1..N` correspond to TDD cycles.

```json
{
  "0": {
    "explore": {
      "status": "done",
      "objective": "",
      "scope": [],
      "non_goals": [],
      "open_questions": [],
      "updated_at": "2026-03-11T00:00:00Z"
    },
    "plan": {
      "status": "done",
      "objective": "",
      "scope": [],
      "non_goals": [],
      "acceptance_criteria": [],
      "stop_and_ask_triggers": [],
      "updated_at": "2026-03-11T00:00:00Z"
    }
  },
  "1": {
    "plan": {
      "status": "done",
      "objective": "",
      "scope": [],
      "non_goals": [],
      "acceptance_criteria": [],
      "stop_and_ask_triggers": [],
      "updated_at": "2026-03-11T00:00:00Z"
    },
    "develop": {
      "status": "pending | in-progress | dev-complete | interrupted",
      "open_questions": [],
      "decisions": [],
      "tests_run": [],
      "next_red_step": "",
      "updated_at": "2026-03-11T00:00:00Z"
    },
    "review": {
      "status": "pending | in-progress | interrupted | changes-requested | approved | blocked",
      "findings": [
        {
          "severity": "MUST-FIX | SHOULD-FIX | NICE-TO-HAVE",
          "file": "",
          "description": "",
          "suggestion": ""
        }
      ],
      "updated_at": "2026-03-11T00:00:00Z"
    },
    "finalize": {
      "status": "pending | done",
      "commit_hash": null,
      "finalized_at": null
    }
  }
}
```

Phase `status` values by phase:

| Phase | Valid statuses |
|---|---|
| explore | `pending \| in-progress \| interrupted \| done` |
| plan | `pending \| in-progress \| interrupted \| done` |
| develop | `pending \| in-progress \| interrupted \| dev-complete` |
| review | `pending \| in-progress \| interrupted \| changes-requested \| approved \| blocked` |
| finalize | `pending \| done` |

### `files-manifest.json`

Tracks file activity keyed by iteration. Append-only. Duplication across iterations is
expected — a file appearing in `affected` in iteration 1 may appear in `active` in
iteration 2, and that is intentional. The `status` view reorganizes by file path across
iterations for impact analysis.

```json
{
  "0": {
    "active": [
      { "path": "", "status": "created | modified | deleted", "commit_hash": "" }
    ],
    "affected": [
      { "path": "", "reason": "", "commit_hash": "" }
    ],
    "references": [
      { "path": "", "type": "exploration | screenshot | external", "commit_hash": "" }
    ],
    "updated_at": "2026-03-11T00:00:00Z"
  }
}
```

`commit_hash` is populated by the tool at the time the file entry is added — not at
finalize time. The tool resolves the current `HEAD` commit hash via git and records it
against each file entry. If the project is not a git repository, `commit_hash` is set
to `null`.

- **active** — files directly created, modified, or deleted this iteration
- **affected** — files discovered to be impacted but not directly touched; used in review
  and impact analysis
- **references** — attachments, screenshots, external notes from exploration

Test run results are not tracked in the artifact schema. Test output is ephemeral and
belongs in the devlog narrative, not in structured state.

### `spec.md`

Living specification for the work item. Created during iteration 0 plan phase. Approval
of iteration 0 plan requires `spec.md` to exist with valid frontmatter and required
sections — enforced by `auggd tools plan approve`. Updated throughout the loop as
understanding evolves.

Required frontmatter: `title`, `status`, `workspace_id`, `created_at`, `updated_at`

Required sections:
- Problem Statement
- Context and Constraints
- Scope and Non-Goals
- Iterations (table: N, objective, status)
- Open Questions
- Decisions Log

### `<topic>.md`

Exploration document. One file per topic explored. Created by the explorer agent in
`attachments/`. Validated by `auggd tools explore approve`.

Required frontmatter: `title`, `description`, `workspace_id`, `iteration`, `created_at`

Required sections:
- Problem Statement — what specific question or uncertainty this topic addresses
- Context — relevant background, constraints, existing patterns in the codebase
- Findings — discovered facts, with sources cited where external
- Candidate Approaches — plausible directions with brief rationale for each
- Open Questions — unresolved items that surfaced during exploration
- Recommended Next Move — explicit handoff signal: proceed to plan, explore further, or escalate

### `.auggd/document-metadata.json`

Project-scoped. Tracks documentation generation state.

```json
{
  "last_commit_hash": "",
  "last_commit_summary": "",
  "generated_at": "2026-03-11T00:00:00Z",
  "documents_updated": [],
  "known_gaps": []
}
```

---

## Phase Gates

Phase transitions are explicit CLI actions. An agent cannot advance a phase by writing
artifacts alone — a gate action is required. The tools layer owns all artifact validation;
skills define principles and tactics, not schema rules.

### Gate Actions

```bash
auggd tools <phase> --ws=<N> approve                                    # advance to next phase
auggd tools <phase> --ws=<N> redirect <target-phase> --note "<reason>"  # send to any phase
auggd tools <phase> --ws=<N> interrupt                                # human-triggered pause
```

`approve` runs prerequisite and validation checks before advancing. If checks fail, it
returns a structured error payload listing what is missing — state is not partially advanced.

`redirect` can target any phase. It sets the target phase status to `in-progress` and
appends the note to that phase's `open_questions` in `iteration-log.json`, giving the
receiving agent explicit context for why it was re-entered.

    `start` vs **re-entry via** `redirect`
    `start` is required only for first entry into a phase. When a phase is re-entered via `redirect`,
    it is already set to `in-progress` by the redirect action — calling `start` again is not required
    and will return an error if the phase entry already exists.

`interrupt` is always human-triggered. It sets the current phase status to `interrupted`
without advancing or reversing state.

### First Entry vs Re-entry

`start` is only required for the **first entry** into a phase for a given iteration. It
initializes the phase entry in `iteration-log.json` and sets status to `in-progress`.

`redirect` handles **re-entry**. It sets the target phase status directly to `in-progress`
and appends the redirect note to that phase's `open_questions`. Calling `start` again on
a phase that already has an entry is an error and will be rejected by the tool.

### Prerequisite Checks (enforced by `approve`)

| Phase | Prerequisite to approve |
|---|---|
| explore | summary non-empty; `<topic>.md` files pass frontmatter and section validation |
| plan (iter 0) | acceptance_criteria non-empty; objective non-empty; `spec.md` passes frontmatter and section validation |
| plan (iter N) | acceptance_criteria non-empty, objective non-empty |
| develop | status = `dev-complete` |
| review | review status explicitly set to `approved` or `changes-requested` |
| finalize | review status = `approved` |

For re-entries via `redirect`, the explore `done` status from a prior iteration satisfies
the `plan start` prerequisite. The tool checks that explore is `done` for any iteration,
not specifically the current one.

---

## `auggd ws info` Output Schema

`ws info` is the **context prime** for every subagent entry point. Its output must orient
a blank-slate agent fully without requiring it to read multiple files.

```json
{
  "id": "AZXyo7HEfomfPS0bTF1uf",
  "slug": "add-user-authentication",
  "title": "",
  "current_phase": "develop",
  "current_iteration": 1,
  "phase_status": "in-progress",
  "last_n_iterations": [
    {
      "n": 1,
      "explore_status": "done",
      "plan_status": "done",
      "develop_status": "in-progress",
      "review_status": "pending",
      "finalize_status": "pending",
      "phases": {
        "explore": { "open_questions": [] },
        "plan": { "open_questions": [] },
        "develop": { "open_questions": [], "decisions": [], "tests_run": [] },
        "review": { "open_questions": [] }
      }
    }
  ],
  "spec_path": "<WS>/spec.md",
  "attachments": ["<WS>/attachments/topic.md"],
  "workspace_path": "<WS>",
  "interrupted": false,
  "redirect_note": null
}
```

`last_n_iterations` returns the last 3 iterations by default. Configurable via
`--last=<N>` flag. Earlier iterations are omitted to manage context window budget.
Agents prioritize the most recent iterations; older entries provide summary context only.

---

## Tools Layer

### CLI Interface

```bash
# Workspace
auggd ws create <slug>
auggd ws list
auggd ws info <N|slug> [--last=<N>]
auggd ws delete <N|slug>

# Install lifecycle
auggd install
auggd uninstall
auggd update
auggd reset

# Phase tools
auggd tools explore --ws=<N|slug> start
auggd tools explore --ws=<N|slug> update --data '<json>'
auggd tools explore --ws=<N|slug> status
auggd tools explore --ws=<N|slug> approve
auggd tools explore --ws=<N|slug> redirect <phase> --note "<reason>"
auggd tools explore --ws=<N|slug> interrupt

auggd tools plan --ws=<N|slug> start
auggd tools plan --ws=<N|slug> create
auggd tools plan --ws=<N|slug> update --data '<json>'
auggd tools plan --ws=<N|slug> status
auggd tools plan --ws=<N|slug> approve
auggd tools plan --ws=<N|slug> redirect <phase> --note "<reason>"
auggd tools plan --ws=<N|slug> interrupt

auggd tools develop --ws=<N|slug> start
auggd tools develop --ws=<N|slug> update --data '<json>'
auggd tools develop --ws=<N|slug> status
auggd tools develop --ws=<N|slug> done
auggd tools develop --ws=<N|slug> approve
auggd tools develop --ws=<N|slug> redirect <phase> --note "<reason>"
auggd tools develop --ws=<N|slug> interrupt

auggd tools review --ws=<N|slug> start
auggd tools review --ws=<N|slug> update --data '<json>'
auggd tools review --ws=<N|slug> status
auggd tools review --ws=<N|slug> approve
auggd tools review --ws=<N|slug> redirect <phase> --note "<reason>"
auggd tools review --ws=<N|slug> interrupt

auggd tools finalize --ws=<N|slug> [--commit]

auggd tools document check
auggd tools document init
auggd tools document update-metadata --data '<json>'

# Files manifest
auggd tools files --ws=<N|slug> add-active --data '<json>'
auggd tools files --ws=<N|slug> add-affected --data '<json>'
auggd tools files --ws=<N|slug> add-reference --data '<json>'
auggd tools files --ws=<N|slug> status
```

### Action Matrix

Tools always operate on the current iteration. The only action that creates a new
iteration is `plan create`. `plan create` requires all phases of the current iteration
to have no unresolved (non-approved) entries before a new iteration can begin.

| Phase | Action | Prerequisite | Effect |
|---|---|---|---|
| `explore` | `start` | workspace exists | creates `attachments/`, sets explore status `in-progress` |
| `explore` | `update` | explore started | merges data into iteration-log explore entry |
| `explore` | `status` | — | reads explore entry from iteration-log |
| `explore` | `approve` | summary non-empty; topic files pass validation | sets status `done`, updates `workspace-metadata.json` |
| `explore` | `redirect <phase>` | — | sets target phase `in-progress`, appends note to target open_questions |
| `explore` | `interrupt` | — | sets status `interrupted` |
| `plan` | `start` | explore status = done; or current iteration > 0 | sets plan status `in-progress` |
| `plan` | `create` | no unresolved phases in current iteration | creates next iteration entry in iteration-log |
| `plan` | `update` | plan started | merges data into current iteration plan entry |
| `plan` | `status` | — | reads current iteration plan entry |
| `plan` | `approve` | acceptance_criteria non-empty; iter 0: spec.md passes validation | sets status `done`, advances current_phase |
| `plan` | `redirect <phase>` | — | sets target phase `in-progress`, appends note |
| `plan` | `interrupt` | — | sets status `interrupted` |
| `develop` | `start` | plan approved for current iteration | sets develop status `in-progress` |
| `develop` | `update` | develop started | merges data into current iteration develop entry |
| `develop` | `status` | — | reads current iteration develop entry |
| `develop` | `done` | develop `in-progress` | sets status `dev-complete`; agent-triggered |
| `develop` | `approve` | status `dev-complete` | advances to review; human-triggered gate |
| `develop` | `redirect <phase>` | — | sets target phase `in-progress`, appends note |
| `develop` | `interrupt` | — | sets status `interrupted` |
| `review` | `start` | develop approved | sets review status `in-progress` |
| `review` | `update` | review started | merges findings into current iteration review entry |
| `review` | `status` | — | reads current iteration review entry |
| `review` | `approve` | review status set to approved or changes-requested via update | sets status `approved` |
| `review` | `redirect <phase>` | — | sets target phase `in-progress`, appends note |
| `review` | `interrupt` | — | sets status `interrupted` |
| `finalize` | (no sub-action) | review `approved` | sets finalized, updates workspace-metadata, optionally commits |
| `document` | `check` | — | verifies git repo, returns HEAD hash and metadata state |
| `document` | `init` | git repo | creates `document-metadata.json` skeleton |
| `document` | `update-metadata` | metadata exists | writes new commit hash and summary |
| `files` | `add-active` | workspace exists | appends to active list in current iteration |
| `files` | `add-affected` | workspace exists | appends to affected list in current iteration |
| `files` | `add-reference` | workspace exists | appends to references list in current iteration |
| `files` | `status` | — | returns files-manifest reorganized by file path across all iterations |

For **iteration 0**, `plan start` requires explore approved. For iterations **1..N** reached via `redirect`,
the prerequisite is satisfied by the existing approved explore entry — explore is not re-gated.


### `develop done` vs `develop approve`

These are distinct and sequential:

- `done` is **agent-triggered**. The agent calls it when the TDD cycle is complete and
  all tests pass. Sets status to `dev-complete`.
- `approve` is **human-triggered**. The human reviews the devlog output and calls it to
  gate the transition to review. Requires `dev-complete` status.

This separation ensures a human checkpoint exists between development and review
regardless of how the agent assessed its own completeness.

### `review update` vs `review approve`

These are distinct:

- `update` is **agent-triggered**. The agent records findings and sets a verdict status
  (`approved`, `changes-requested`, or `blocked`) via `update --data`. This is the agent's assessment.
- `approve` is **human-triggered**. It confirms the verdict and gates the transition to finalize.
  It requires that the review status has already been explicitly set by the agent via `update`.

This ensures the human has reviewed the agent's findings before the iteration can close.

### `review approve` and verdict flow

`review approve` does not set the review verdict — it confirms it. The flow is:

1. The reviewer agent calls `review update` with `status` set to `approved` or
   `changes-requested` as part of recording findings.
2. The human reads the review output and calls `review approve` to gate the transition.
3. `review approve` requires the status to already be explicitly set to `approved` or
   `changes-requested` — it will reject if status is still `pending`, `in-progress`,
   or `blocked`.

This means `review approve` with status `changes-requested` advances to the next phase
(typically a redirect back to develop or plan), not just when `approved`.

### Tool Response Format

All actions return JSON to stdout, exit 0. Errors are in the payload.

```json
// Success
{ "ok": true, "data": { ... } }

// Failure
{
  "ok": false,
  "error": "MISSING_PLAN",
  "message": "No plan entry found for iteration 1. Run plan create first.",
  "missing": ["iteration-log.json#1.plan"]
}
```

### OpenCode Tool Wrappers

Each phase has a `.opencode/tools/oag-<phase>.ts` with named exports. OpenCode registers
them as `oag-<phase>_<action>` tools. Each wrapper calls the Python CLI via `Bun.$`.

```typescript
export const start = tool({
  description: "Start explore phase for a workspace.",
  args: { ws: tool.schema.string().describe("Workspace number or slug") },
  async execute(args) {
    return await Bun.$`auggd tools explore --ws=${args.ws} start`.text()
  },
})
```

`oag-ws.ts` exposes workspace management actions (`info`, `create`, `list`, `delete`, `resume`)
as agent-callable tools following the same pattern. Commands (`oag-status`, `oag-resume`)
are human-facing; their corresponding tool wrappers in `oag-ws.ts` are agent-facing.
These follow different naming conventions by design.

Tool files are committed to git. `.auggd/` is gitignored.

---

## Skills Architecture

Skills are split into two layers. Template skills are omitted — artifact validation is
owned by the tools layer, eliminating the maintenance coupling between skill content
and validation rules.

**1. Core Principles (2 skills)**

| Skill | Purpose |
|---|---|
| `oag-spec-standards` | Spec writing principles — outcome, constraint, and acceptance levels |
| `oag-dev-standards` | TDD philosophy — Classical vs London, greenfield vs brownfield, shape vs flow |

**2. Phase Models + Tactics (10 skills)**

| Skill | Purpose |
|---|---|
| `oag-exploration-model` | Exploration principles — what exploration produces, when it is done |
| `oag-exploration-tactics` | Decision guidance for the explore phase + relevant tool reference |
| `oag-planning-model` | Planning principles — what a good iteration looks like, TDD sizing |
| `oag-planning-tactics` | Decision guidance for the plan phase + relevant tool reference |
| `oag-development-model` | Development principles — RED/GREEN/REFACTOR, greenfield vs brownfield modes |
| `oag-development-tactics` | Decision guidance for the develop phase + relevant tool reference |
| `oag-review-model` | Review principles — intent alignment, smell detection, feedback quality |
| `oag-review-tactics` | Decision guidance for the review phase + relevant tool reference |
| `oag-finalize-model` | Finalize principles — what done means, commit scope |
| `oag-finalize-tactics` | Decision guidance for the finalize phase + relevant tool reference |

**3. Documentation (2 skills — project-scoped)**

| Skill | Purpose |
|---|---|
| `oag-documentation-model` | Documentation principles — Diataxis, scope, generation triggers |
| `oag-documentation-standards` | Style, Mermaid usage, structure conventions |

Total: **14 skills**

### Tactics Skill Structure

Each tactics skill follows this structure:

1. **Situational assessment** — what to check first, how to read current state from `ws info`
2. **Decision guidance** — how to navigate forks in the current phase
3. **Tool reference** — which `oag-<phase>_<action>` tools are relevant and under what
   conditions; tools from other phases are omitted

---

## Agents

### Primary

**`auggd`**
- Entry point for user interaction
- Delegates to subagents based on user intent
- Handles status and resume flows directly (cross-phase reasoning)
- Does not execute phase work itself

### Subagents (all `hidden: true`)

| Agent | Phase | Skills loaded |
|---|---|---|
| `oag-explorer` | explore | `oag-exploration-model`, `oag-exploration-tactics`, `oag-spec-standards` |
| `oag-planner` | plan | `oag-planning-model`, `oag-planning-tactics`, `oag-dev-standards`, `oag-spec-standards` |
| `oag-developer` | develop | `oag-development-model`, `oag-development-tactics`, `oag-dev-standards` |
| `oag-reviewer` | review | `oag-review-model`, `oag-review-tactics`, `oag-dev-standards` |
| `oag-finalizer` | finalize | `oag-finalize-model`, `oag-finalize-tactics` |
| `oag-documenter` | document | `oag-documentation-model`, `oag-documentation-standards` |

### Permissions Pattern

All agents use `oag-*` tool wrappers for JSON state mutations. Direct file writes are
scoped to narrative markdown artifacts only.

| Agent | Edit | Bash |
|---|---|---|
| `oag-explorer` | `attachments/` only | read-only |
| `oag-planner` | workspace root (`spec.md`) only | read-only |
| `oag-developer` | unrestricted (code files) | curated — no `git push`, no destructive ops |
| `oag-reviewer` | deny | read-only |
| `oag-finalizer` | deny | git commit allowed; no push |
| `oag-documenter` | `docs/` only | read-only |

### Agent Bootstrap Contract

Every subagent invocation begins with:

```
1. oag-ws_info <N> [--last=3]    # context prime via tool wrapper
2. Load relevant skills
3. Read redirect_note if present  # understand why re-entered
4. Proceed with phase work
```

Agents do not scan workspace directories to determine state. The `ws info` output is
the single orientation source.

---

## Commands

Commands are human-facing entry points. All commands are `subtask: true` and route
directly to their subagent. `oag-status` and `oag-resume` route to `auggd` for
cross-phase reasoning.

| Command | Agent | Parameters |
|---|---|---|
| `oag-explore` | `oag-explorer` | `$1` = workspace ref |
| `oag-plan` | `oag-planner` | `$1` = workspace ref |
| `oag-develop` | `oag-developer` | `$1` = workspace ref |
| `oag-review` | `oag-reviewer` | `$1` = workspace ref |
| `oag-finalize` | `oag-finalizer` | `$1` = workspace ref |
| `oag-document` | `oag-documenter` | none |
| `oag-status` | `auggd` | `$1` = workspace ref |
| `oag-resume` | `auggd` | `$1` = workspace ref |

---

## Configuration

### Hierarchy

```
auggd.toml  <  OAG_* env vars  <  CLI flags
```

### `auggd.toml`

Generated by `auggd install`. Located at `.auggd/auggd.toml`. Gitignored.

```toml
[workspace]
dir = ".auggd/workspace"

[docs]
dir = "docs"

[defaults]
model = "opencode/gpt-5-nano"

[agents.models]
# explorer = "anthropic/claude-sonnet-4-6"
# developer = "anthropic/claude-sonnet-4-6"

[commands.models]
# develop = "anthropic/claude-sonnet-4-6"
```

### Environment Variables

| Variable | Description | Default |
|---|---|---|
| `OAG_WORKSPACE_DIR` | Workspace root path | `<project>/.auggd/workspace` |
| `OAG_DOCS_DIR` | Project docs path | `<project>/docs` |
| `OAG_DEFAULT_MODEL` | Default model | `opencode/gpt-5-nano` |
| `OAG_<AGENT>_MODEL` | Per-agent model override | — |
| `OAG_<COMMAND>_MODEL` | Per-command model override | — |

Agent/command name: uppercase without `oag-` prefix.
Examples: `OAG_DEVELOPER_MODEL`, `OAG_DEVELOP_MODEL`, `OAG_AUGGD_MODEL`

Path values support `~` and `$VARNAME` expansion.

---

## Install Lifecycle

### `auggd install`

Run once from project root.

Creates:
```
.auggd/                              # gitignored
  auggd.toml
  install-manifest.json

.opencode/                           # committed to git
  agents/
    auggd.md
    oag-explorer.md
    oag-planner.md
    oag-developer.md
    oag-reviewer.md
    oag-finalizer.md
    oag-documenter.md
  commands/
    oag-explore.md
    oag-plan.md
    oag-develop.md
    oag-review.md
    oag-finalize.md
    oag-document.md
    oag-status.md
    oag-resume.md
  skills/
    oag-spec-standards/SKILL.md
    oag-dev-standards/SKILL.md
    oag-exploration-model/SKILL.md
    oag-exploration-tactics/SKILL.md
    oag-planning-model/SKILL.md
    oag-planning-tactics/SKILL.md
    oag-development-model/SKILL.md
    oag-development-tactics/SKILL.md
    oag-review-model/SKILL.md
    oag-review-tactics/SKILL.md
    oag-finalize-model/SKILL.md
    oag-finalize-tactics/SKILL.md
    oag-documentation-model/SKILL.md
    oag-documentation-standards/SKILL.md
  tools/
    oag-explore.ts
    oag-plan.ts
    oag-develop.ts
    oag-review.ts
    oag-finalize.ts
    oag-document.ts
    oag-files.ts
    oag-ws.ts
```

`install-manifest.json` records every file path written, enabling clean uninstall.

### `auggd uninstall`

Removes `.auggd/` entirely. Removes all files listed in `install-manifest.json` from
`.opencode/`. Pre-existing `.opencode/` content is untouched.

### `auggd update`

Updates the `model:` frontmatter line in all managed agent and command files to reflect
current config and env settings. Content body and other frontmatter fields are not modified.

### `auggd reset`

Restores all `.opencode/` files managed by auggd to their bundled defaults. `.auggd/`
config and workspace data are not affected. Requires confirmation: `Type 'yes' to confirm:`.

---

## Source Layout

```
src/open_auggd/
├── __init__.py
├── cli/
│   ├── __init__.py
│   ├── main.py            # click group: auggd
│   ├── install.py         # install, uninstall, update, reset
│   ├── workspace.py       # ws create, list, info, delete
│   └── tools.py           # tools <phase> <action> routing
├── config/
│   ├── __init__.py
│   └── settings.py        # config loading: TOML + env + CLI, path expansion
├── workspace/
│   ├── __init__.py
│   ├── manager.py         # WorkspaceManager: create/list/resolve/delete/info
│   ├── models.py          # dataclasses, enums, JSON schemas for all artifacts
│   └── slugify.py         # slug normalization
├── install/
│   ├── __init__.py
│   ├── installer.py       # install/uninstall logic, manifest management
│   └── updater.py         # model frontmatter update logic
├── tools/
│   ├── __init__.py
│   ├── base.py            # ToolResult, gate enforcement, artifact validation helpers
│   ├── explore.py
│   ├── plan.py
│   ├── develop.py
│   ├── review.py
│   ├── finalize.py
│   ├── document.py
│   └── files.py           # files-manifest operations
└── templates/
    ├── agents/
    ├── commands/
    ├── skills/
    └── tools/

tests/
├── unit/
│   ├── test_config.py
│   ├── test_slugify.py
│   ├── test_workspace_manager.py
│   ├── test_workspace_models.py
│   ├── test_tools_base.py
│   ├── test_tools_explore.py
│   ├── test_tools_plan.py
│   ├── test_tools_develop.py
│   ├── test_tools_review.py
│   ├── test_tools_finalize.py
│   ├── test_tools_document.py
│   ├── test_tools_files.py
│   └── test_updater.py
└── integration/
    └── test_install.py
```

---

## Dependencies

| Package | Reason | Condition |
|---|---|---|
| `click>=8.0` | CLI framework | always |
| `uuid7>=0.1` | UUID7 generation | always |
| `tomli>=2.0` | TOML reading | `python_version < "3.11"` |

No Jinja2, no PyYAML, no external template libraries.

---

## Build Order

### Phase 3a — Core (Python CLI + Tools)

1. `pyproject.toml` — verify name, scripts entry point, dependencies
2. `config/settings.py` — config loading foundation
3. `workspace/slugify.py` — slug normalization
4. `workspace/models.py` — all dataclasses, enums, artifact schemas
5. `workspace/manager.py` — workspace CRUD + `ws info` output contract
6. `install/installer.py` + `install/updater.py` — install lifecycle
7. `tools/base.py` — ToolResult, gate enforcement, artifact validation helpers
8. `tools/explore.py` + `tools/plan.py` + `tools/develop.py`
9. `tools/review.py` + `tools/finalize.py` + `tools/document.py`
10. `tools/files.py` — files-manifest operations
11. `cli/` — wire all tools into click commands
12. `templates/tools/*.ts` — TypeScript wrappers for all tool actions
13. Unit + integration tests

### Phase 3b — Content (Templates)

1. Core principles skills: `oag-spec-standards`, `oag-dev-standards`
2. Phase model skills (5): exploration, planning, development, review, finalize
3. Phase tactics skills (5): exploration, planning, development, review, finalize
4. Documentation skills (2): model + standards
5. Subagents (6): explorer, planner, developer, reviewer, finalizer, documenter
6. Primary agent (1): auggd
7. Commands (8): explore, plan, develop, review, finalize, document, status, resume

---

## Acceptance Criteria

Structured as vertical slices for incremental manual verification.

### Slice 1 — Install Lifecycle

- [ ] `auggd install` creates `.auggd/` and `.opencode/` with all listed files
- [ ] `install-manifest.json` records every written path
- [ ] `auggd uninstall` removes only managed files; pre-existing `.opencode/` content untouched
- [ ] `auggd update` modifies only `model:` frontmatter line; content body unchanged
- [ ] `auggd reset` restores managed files to bundled defaults with confirmation prompt

### Slice 2 — Workspace Management

- [ ] `auggd ws create <slug>` creates workspace dir, `workspace-metadata.json`, empty `iteration-log.json`, empty `files-manifest.json`
- [ ] `auggd ws list` returns all workspaces sorted by creation time
- [ ] `auggd ws info <N>` returns full context prime schema
- [ ] `auggd ws info <N> --last=<N>` respects iteration limit
- [ ] `auggd ws delete <N>` removes workspace dir

### Slice 3 — Phase Tools and Gate Mechanics

#### Tool Responses

- [ ] All tool actions return valid JSON, exit 0
- [ ] Error payloads include `error` code, human-readable `message`, and `missing` array where applicable

#### explore
- [ ] `start` creates `attachments/`, sets explore status `in-progress`
- [ ] `update` merges data without overwriting unrelated fields
- [ ] `status` returns current explore entry
- [ ] `approve` validates `<topic>.md` frontmatter and required sections; returns structured error on failure without advancing state
- [ ] `approve` sets status `done`, updates `workspace-metadata.json`
- [ ] `redirect <phase>` sets target phase `in-progress`, appends note to target open_questions
- [ ] `interrupt` sets status `interrupted` without advancing or reversing state

#### plan
- [ ] `start` requires explore approved; sets plan status `in-progress`
- [ ] `create` blocked when any phase of current iteration is unresolved
- [ ] `create` creates next iteration entry in `iteration-log.json`
- [ ] `update` merges data without overwriting unrelated fields
- [ ] `status` returns current iteration plan entry
- [ ] `approve` on iteration 0 validates `spec.md` frontmatter and required sections; returns structured error on failure without advancing state
- [ ] `approve` on iteration N requires acceptance_criteria and objective non-empty
- [ ] `approve` sets status `done`, updates `workspace-metadata.json`
- [ ] `redirect <phase>` sets target phase `in-progress`, appends note to target open_questions
- [ ] `interrupt` sets status `interrupted` without advancing or reversing state

#### develop
- [ ] `start` requires plan approved for current iteration; sets develop status `in-progress`
- [ ] `update` merges data without overwriting unrelated fields
- [ ] `status` returns current iteration develop entry
- [ ] `done` requires status `in-progress`; sets status `dev-complete`; agent-triggered
- [ ] `approve` requires status `dev-complete`; advances to review; human-triggered
- [ ] `redirect <phase>` sets target phase `in-progress`, appends note to target open_questions
- [ ] `interrupt` sets status `interrupted` without advancing or reversing state

#### review
- [ ] `start` requires develop approved; sets review status `in-progress`
- [ ] `update` merges findings without overwriting unrelated fields
- [ ] `status` returns current iteration review entry
- [ ] `approve` requires review status explicitly set; sets status `approved`
- [ ] `redirect <phase>` sets target phase `in-progress`, appends note to target open_questions
- [ ] `interrupt` sets status `interrupted` without advancing or reversing state

#### finalize
- [ ] requires review status `approved`; returns structured error otherwise
- [ ] sets iteration finalized, updates `workspace-metadata.json`
- [ ] `--commit` flag triggers git commit and records commit hash in `iteration-log.json`

#### files 

- [ ] `files add-active`, `add-affected`, `add-reference` append to current iteration entry
- [ ] `files status` returns manifest reorganized by file path across all iterations
- [ ] Duplication across iterations is preserved as expected


### Slice 4 — Content (Phase 3b)

- [ ] All 14 `SKILL.md` files contain substantive content, no placeholders
- [ ] All 7 agent files contain full frontmatter and body
- [ ] All 8 command files contain full frontmatter and steps
- [ ] No agent reads raw artifact files for state — all state access via `oag-*` tools
- [ ] All agents begin with `oag-ws_info` as bootstrap step
- [ ] Tactics skills include tool reference section scoped to their phase only
- [ ] `auggd install` deploys all content without errors

---

## Out of Scope for Phase 3

- Multi-user or team workspace sharing
- Autonomous phase transitions (human gate approval required)
- Context window compaction (deferred — agents prioritize last 3 iterations via `--last`)
- Cross-workspace dependency tracking
- Full autonomous brownfield codebase priming
- Push / PR automation (manual user action after finalize)
