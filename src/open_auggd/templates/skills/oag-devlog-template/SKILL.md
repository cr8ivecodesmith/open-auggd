---
name: oag-devlog-template
description: Template and structure for iter-N-devlog.md — the narrative development log companion to iter-N-devlog.json.
compatibility: opencode
---

# Devlog Template

Artifact: `<WS>/develop/iter-N-devlog.md`
JSON counterpart: `<WS>/develop/iter-N-devlog.json` (managed by `auggd tools develop`)
Type: append-only — add new entries below existing ones; do not rewrite prior entries

## When to write

Write a devlog entry:
- At the start of a session (goal for this session)
- After completing a meaningful step (RED → GREEN, or REFACTOR completion)
- Before stopping (current assessment, next step)
- After running quality gates (record results)

One file per iteration. Multiple entries per file as work progresses.

## Template

```markdown
# Devlog — iter-<N> — <short title matching iter-N-plan.md>

## Status
- Workspace: <workspace-id>
- Iteration: <N>
- Status: in_progress | dev_complete

---

## Entry — <ISO 8601 timestamp>

### Goal for this session
<What you intend to accomplish in this session. One paragraph.>

### What changed
<Describe what was implemented or modified. Be specific — the reviewer will read this.>

### Files touched
- `path/to/file.py` — <what changed and why>
- `path/to/test_file.py` — <what tests were added/modified>

### Tests run
| Command | Result |
|---|---|
| `pytest tests/unit/test_foo.py` | 4 passed |
| `pytest tests/` | 12 passed |

### Other checks
| Check | Command | Result |
|---|---|---|
| Lint | `ruff check src/` | no issues |
| Typecheck | `mypy src/` | no errors |

### Scenarios addressed
- [x] S1 — <title>: <brief note on how it's addressed>
- [ ] S2 — <title>: not yet started
- [-] S3 — <title>: partial — <what remains>

### Current assessment
<Is the implementation correct? What is still risky? What surprised you?
Be honest — the reviewer will use this to calibrate their review.>

### Next smallest RED step
<Exact description of the next failing test to write. One sentence.>

### Open questions / blockers
- <question or blocker, if any>
```

## Writing guidance

**Files touched**: list every file modified, including test files. A reviewer should be able
to locate the changes from this list without running git.

**Tests run**: always include the command exactly as run, not a paraphrase. Include counts.
If tests failed, record the failure — do not hide failures.

**Scenarios addressed**: use the scenario IDs from `iter-N-plan.md`. Mark `[x]` when done,
`[ ]` when not started, `[-]` when partial. This is the primary way reviewers assess
acceptance criteria coverage.

**Current assessment**: write for the reviewer, not yourself. They need to understand what
you think is solid, what is risky, and what is incomplete. Do not write "looks good."

**Next smallest RED step**: this should be a literal test description. If you are done,
write "none — ready for review." This tells the reviewer whether the cycle is complete.

## Relationship to iter-N-devlog.json

The JSON counterpart is updated via `auggd tools develop update`. It tracks structured
fields (`files_touched`, `tests_run`, `blockers`, `next_red_step`, `status`). The markdown
devlog is the narrative explanation. Keep both in sync — do not update one without the other.
