---
name: oag-explore
description: Run the explore phase for a workspace. Gather repo and external facts, clarify the problem, and produce exploration artifacts.
agent: oag-explorer
subtask: true
model: opencode/gpt-5-nano
---

Workspace: `$1`
Topic / request: `$2`

Do:
1) Load skills: `oag-exploration-workflow`

2) Run `auggd tools explore --ws=$1 status` to check current exploration state.
   If not yet started, run `auggd tools explore --ws=$1 start`.

3) If `$2` is provided, use it as the exploration topic. If not, ask the user to describe
   what they want to explore before proceeding.

4) Clarify the problem in plain language. If the request is vague, ask one clarifying
   question before exploring widely.

5) Inspect the repo for relevant surfaces: paths, entry points, existing patterns, test and
   build commands, boundaries. Focus on what is relevant to the topic.

6) Gather external information if libraries, APIs, tools, or current best practices matter.
   Cite sources in the narrative.

7) Surface 2–5 plausible directions when multiple solutions exist. Evaluate each against
   the identified constraints.

8) Write the exploration narrative to the workspace `explore/<topic>.md` file, following
   the structure in `oag-exploration-workflow`.

9) When exploration is complete and at least one plausible direction exists, run:
   `auggd tools explore --ws=$1 done`

10) Summarize findings and recommended next move to the user.
    Suggested follow-on: `/oag-plan $1`
