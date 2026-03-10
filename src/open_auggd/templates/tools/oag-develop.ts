import { tool } from "@opencode-ai/plugin";

export const start = tool({
  description: "Start development of iteration N. Requires iter-N-plan.json to exist and be ready.",
  args: {
    ws: tool.schema.string().describe("Workspace number or slug substring"),
    n: tool.schema.number().describe("Iteration number"),
  },
  async execute(args) {
    return await Bun.$`auggd tools develop --ws=${args.ws} start ${args.n}`.text();
  },
});

export const update = tool({
  description: "Merge JSON fields into the devlog for iteration N.",
  args: {
    ws: tool.schema.string().describe("Workspace number or slug substring"),
    n: tool.schema.number().describe("Iteration number"),
    data: tool.schema.string().describe("JSON patch string"),
  },
  async execute(args) {
    return await Bun.$`auggd tools develop --ws=${args.ws} update ${args.n} --data ${args.data}`.text();
  },
});

export const status = tool({
  description: "Return the devlog status for iteration N.",
  args: {
    ws: tool.schema.string().describe("Workspace number or slug substring"),
    n: tool.schema.number().describe("Iteration number"),
  },
  async execute(args) {
    return await Bun.$`auggd tools develop --ws=${args.ws} status ${args.n}`.text();
  },
});

export const done = tool({
  description: "Mark development of iteration N as complete.",
  args: {
    ws: tool.schema.string().describe("Workspace number or slug substring"),
    n: tool.schema.number().describe("Iteration number"),
  },
  async execute(args) {
    return await Bun.$`auggd tools develop --ws=${args.ws} done ${args.n}`.text();
  },
});
