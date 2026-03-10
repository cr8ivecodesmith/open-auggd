import { tool } from "@opencode-ai/sdk";

export const start = tool({
  description: "Start the explore phase. Creates explore/ structure and attachments registry.",
  args: { ws: tool.schema.string().describe("Workspace number or slug substring") },
  async execute(args) {
    return await Bun.$`auggd tools explore --ws=${args.ws} start`.text();
  },
});

export const status = tool({
  description: "Return current explore phase status for the workspace.",
  args: { ws: tool.schema.string().describe("Workspace number or slug substring") },
  async execute(args) {
    return await Bun.$`auggd tools explore --ws=${args.ws} status`.text();
  },
});

export const done = tool({
  description: "Mark the explore phase as done.",
  args: { ws: tool.schema.string().describe("Workspace number or slug substring") },
  async execute(args) {
    return await Bun.$`auggd tools explore --ws=${args.ws} done`.text();
  },
});
