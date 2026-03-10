---
name: oag-documentation-standards
description: Standards for project documentation using Diataxis, layered structure, metadata tracking, and Mermaid diagrams where they help.
compatibility: opencode
---

# Documentation Standards

## Where docs live

All documentation lives under `docs/`. Generation state is tracked in
`.auggd/document-metadata.json`. Do not create documentation files outside these locations.

## Diataxis categories

Every doc belongs to exactly one category. Choose based on reader goal:

| Category | Reader goal | Format |
|---|---|---|
| **Tutorial** | Learn by doing | Guided walkthrough, concrete steps, single goal |
| **How-to** | Accomplish a specific task | Step-by-step, assumes some knowledge, goal-oriented |
| **Reference** | Look up accurate information | Systematic, complete, describes what exists |
| **Explanation** | Understand why / how | Discursive, conceptual, discusses decisions and tradeoffs |

Do not mix categories in a single document.

## Layered understanding

Structure docs to support progressive disclosure:

- **Layer 0 — Get productive**: quickstart, install, first run. Minimal prerequisites assumed.
- **Layer 1 — Big picture**: architecture overview, key concepts, how pieces fit together.
- **Layer 2 — Where to change X**: module map, extension points, common modification patterns.
- **Layer 3 — Lookup / operations**: full CLI reference, config options, troubleshooting.

Most users read Layer 0 once and return to Layer 3 repeatedly. Design for both.

## What to document

Update docs when:
- Setup or installation steps change
- CLI commands, flags, or config options change
- Architecture or module boundaries change
- New ownership units are added (new agent, command, or skill)
- Behavior that affects users changes
- Onboarding pain reveals a gap

Do not update docs when nothing relevant changed. Stale docs are worse than absent docs.

## Content rules

- Prefer concrete examples over abstract descriptions
- Prefer actual paths and commands over prose descriptions of paths and commands
- Name the owner of each behavior (which command, which agent, which module)
- Use `auggd <subcommand>` examples with real flags, not pseudocode
- Keep each doc focused on one purpose — split if it serves two goals

## Mermaid diagrams

Use Mermaid where it materially improves understanding:
- Architecture diagrams showing module relationships
- Phase gate flow (explore → plan → develop → review → finalize → document)
- Sequence diagrams for multi-step tool interactions

Do not use Mermaid for:
- Information that prose describes better
- Structure that does not exist in the code
- Decoration

## Metadata schema

`.auggd/document-metadata.json`:

```json
{
  "last_commit_hash": "<git SHA>",
  "last_commit_summary": "brief description of what changed",
  "generated_at": "2026-03-10T00:00:00Z",
  "documents_updated": ["docs/reference/cli.md"],
  "known_gaps": ["API reference not yet generated"]
}
```

Update via `auggd tools document update-metadata --data '<json>'` after each documentation
session. Never write to this file directly.

## Quality bar

A documentation session is complete when:
- All affected docs are updated and accurate to the current codebase
- `document-metadata.json` reflects the current HEAD hash
- Known gaps are recorded honestly in `known_gaps`
- No doc references behavior that no longer exists
- No doc is aspirational — only describe what is implemented

## Maintenance rule

Documentation drifts. When in doubt:
1. Check `last_commit_hash` against HEAD via `auggd tools document check`
2. Run `git log --oneline <last_commit_hash>..HEAD` to see what changed
3. Update only what changed — do not rewrite docs that are still accurate
