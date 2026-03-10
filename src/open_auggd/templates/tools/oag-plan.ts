import { tool } from "@opencode-ai/sdk";

export const start = tool({
  description: "Start the plan phase. Requires explore phase to be done.",
  args: { ws: tool.schema.string().describe("Workspace number or slug substring") },
  async execute(args) {
    return await Bun.$`auggd tools plan --ws=${args.ws} start`.text();
  },
});

export const iter_create = tool({
  description: "Create the next iteration plan (iter-N-plan.json and .md).",
  args: { ws: tool.schema.string().describe("Workspace number or slug substring") },
  async execute(args) {
    return await Bun.$`auggd tools plan --ws=${args.ws} iter create`.text();
  },
});

export const iter_status = tool({
  description: "Return the status of a specific iteration plan.",
  args: {
    ws: tool.schema.string().describe("Workspace number or slug substring"),
    n: tool.schema.number().describe("Iteration number"),
  },
  async execute(args) {
    return await Bun.$`auggd tools plan --ws=${args.ws} iter status ${args.n}`.text();
  },
});

export const iter_done = tool({
  description: "Mark an iteration plan as ready for development.",
  args: {
    ws: tool.schema.string().describe("Workspace number or slug substring"),
    n: tool.schema.number().describe("Iteration number"),
  },
  async execute(args) {
    return await Bun.$`auggd tools plan --ws=${args.ws} iter done ${args.n}`.text();
  },
});
