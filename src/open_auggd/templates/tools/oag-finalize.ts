import { tool } from "@opencode-ai/plugin";

export const iter = tool({
  description: "Finalize iteration N. Requires approved review. Optionally commits.",
  args: {
    ws: tool.schema.string().describe("Workspace number or slug substring"),
    n: tool.schema.number().describe("Iteration number"),
    commit: tool.schema.boolean().optional().describe("If true, auto-commit after finalize"),
  },
  async execute(args) {
    const commitFlag = args.commit ? "--commit" : "";
    return await Bun.$`auggd tools finalize --ws=${args.ws} iter ${args.n} ${commitFlag}`.text();
  },
});
