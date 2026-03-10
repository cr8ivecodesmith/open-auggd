---
name: oag-document
description: Update project documentation under docs/ based on recent changes. Tracks generation state in .auggd/document-metadata.json.
agent: oag-documenter
subtask: true
model: opencode/gpt-5-nano
---

Do:
1) Load skills: `oag-documentation-workflow`, `oag-documentation-standards`

2) Run `auggd tools document check` to verify the project is a git repository and to get
   the current HEAD hash and metadata state.
   If not a git repo, stop and warn the user.

3) If `document-metadata.json` is absent, run `auggd tools document init`.

4) Compare `last_commit_hash` from the metadata to HEAD. If they match, docs are current.
   Confirm with the user before regenerating.

5) Run `git log --oneline <last_commit_hash>..HEAD` to identify what changed since last
   documentation generation.

6) Determine which docs areas are affected by the changes:
   - New or changed CLI commands or configuration options
   - Changed architecture or module structure
   - New setup or installation steps
   - Changes that affect onboarding or user-facing behavior

7) Update only the relevant files under `docs/`. Organize by Diataxis purpose:
   - Tutorial — learning-oriented, step-by-step
   - How-to — task-oriented, achieves a specific goal
   - Reference — accurate and complete description of what exists
   - Explanation — conceptual, discusses decisions and tradeoffs

8) Use Mermaid diagrams where they materially improve understanding. Do not add diagrams
   for decoration.

9) After updating docs, run:
   `auggd tools document update-metadata --data '{"last_commit_hash": "<HEAD>", "last_commit_summary": "...", "documents_updated": [...], "known_gaps": [...]}'`

10) Summarize what was updated, what was left unchanged, and any known gaps recorded.
