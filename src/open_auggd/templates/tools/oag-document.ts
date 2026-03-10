import { tool } from "@opencode-ai/plugin";

export const check = tool({
  description: "Verify git repo and return current commit hash and document metadata status.",
  args: {},
  async execute(_args) {
    return await Bun.$`auggd tools document check`.text();
  },
});

export const init = tool({
  description: "Initialize .auggd/document-metadata.json for a git repo.",
  args: {},
  async execute(_args) {
    return await Bun.$`auggd tools document init`.text();
  },
});

export const update_metadata = tool({
  description: "Update document metadata with new commit hash and summary.",
  args: {
    data: tool.schema.string().describe("JSON patch string"),
  },
  async execute(args) {
    return await Bun.$`auggd tools document update-metadata --data ${args.data}`.text();
  },
});
