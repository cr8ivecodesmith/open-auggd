import { tool } from "@opencode-ai/plugin";

export const start = tool({
  description: "Start the review for iteration N. Requires dev_complete status.",
  args: {
    ws: tool.schema.string().describe("Workspace number or slug substring"),
    n: tool.schema.number().describe("Iteration number"),
  },
  async execute(args) {
    return await Bun.$`auggd tools review --ws=${args.ws} start ${args.n}`.text();
  },
});

export const update = tool({
  description: "Merge review findings into the review JSON for iteration N.",
  args: {
    ws: tool.schema.string().describe("Workspace number or slug substring"),
    n: tool.schema.number().describe("Iteration number"),
    data: tool.schema.string().describe("JSON patch string"),
  },
  async execute(args) {
    return await Bun.$`auggd tools review --ws=${args.ws} update ${args.n} --data ${args.data}`.text();
  },
});

export const done = tool({
  description: "Set the review outcome for iteration N.",
  args: {
    ws: tool.schema.string().describe("Workspace number or slug substring"),
    n: tool.schema.number().describe("Iteration number"),
    review_status: tool.schema.string().describe("One of: blocked, changes_requested, approved"),
  },
  async execute(args) {
    return await Bun.$`auggd tools review --ws=${args.ws} done ${args.n} ${args.review_status}`.text();
  },
});
