---
name: oag-documentation-workflow
description: Phase skill for documentation work: update project-level docs under docs/ based on recent changes, and track generation state in .auggd/document-metadata.json.
compatibility: opencode
---

# Documentation Workflow

Phase: document
State artifact: `.auggd/document-metadata.json`
Documentation lives in: `docs/`

Note: documentation is project-scoped, not workspace-scoped. It reflects the full project,
not a single workspace or iteration.

## What to do

1. Call `auggd tools document check` first. This verifies the project is a git repository
   and returns the current HEAD hash plus metadata state. If the project is not a git repo,
   stop and warn.

2. If `document-metadata.json` is absent, call `auggd tools document init` to create it
   with the current HEAD hash.

3. Compare `last_commit_hash` from metadata to HEAD. If they match, docs are current —
   check with the user before re-generating.

4. Identify which areas changed since last generation:
   - New features or behavior changes (from git log)
   - Changed CLI commands or configuration options
   - Changed architecture or module boundaries
   - New setup or installation steps
   - Changes that affect onboarding

5. Update only the relevant docs. Do not rewrite docs that have not changed.

6. Organize docs by Diataxis purpose:
   - **Tutorial** — learning-oriented, walks through a specific task step by step
   - **How-to** — task-oriented, achieves a specific goal (assumes some knowledge)
   - **Reference** — information-oriented, describes the system accurately and completely
   - **Explanation** — understanding-oriented, discusses concepts and decisions

7. Use Mermaid diagrams where they materially improve understanding (architecture, flows,
   phase gates). Do not add diagrams for the sake of diagrams.

8. Call `auggd tools document update-metadata --data '<json>'` after updating docs:

   ```json
   {
     "last_commit_hash": "<HEAD hash>",
     "last_commit_summary": "brief description of what changed",
     "documents_updated": ["docs/reference/cli.md", "docs/how-to/install.md"],
     "known_gaps": ["API reference not yet generated"]
   }
   ```

   `documents_updated` and `known_gaps` are set-union merged on each update call.

## Documentation quality bar

Good project docs:
- Are accurate to the current codebase — do not document aspirational behavior
- Prefer paths, commands, concrete examples, and ownership over abstract descriptions
- Layer from simple to detailed: quickstart → how-to → reference → explanation
- Keep each doc focused on one purpose (Diataxis category)
- Record known gaps honestly rather than leaving docs stale silently

## What NOT to do

- Do not update docs if the project is not a git repo (tool will warn, but confirm first).
- Do not modify `.auggd/document-metadata.json` directly — use `auggd tools document`.
- Do not generate docs from memory — inspect the actual codebase.
- Do not add Mermaid diagrams that invent structure not present in the code.
- Do not skip `update-metadata` — the hash is how future sessions know what is current.

## Exit criteria

- Affected docs updated and accurate to the current codebase
- `document-metadata.json` reflects the current HEAD hash
- Known gaps recorded in metadata `known_gaps`
- Diataxis categories respected

## Handoff

Usually ends the loop. Re-route if documentation reveals:
- Missing facts → `oag-explore`
- Planning drift → `oag-plan`
- Implementation gaps → `oag-develop`
