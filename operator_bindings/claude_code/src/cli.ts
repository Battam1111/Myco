#!/usr/bin/env node
// CLI entry point for the Myco MCP server.
//
// Run via `myco-mcp-claude-code` (after `npm install -g .`) or via
// `node --experimental-strip-types src/cli.ts` for local development.
//
// Reads MCP requests from stdin, writes responses to stdout (standard MCP
// stdio transport). The substrate subprocess is spawned lazily on first
// tool call.

import { McpServer } from "./mcp_server.ts";

async function main(): Promise<void> {
  const server = new McpServer({
    substrate: {
      // Respect MYCO_SUBSTRATE_BIN env var; falls back to "myco-substrate" PATH lookup.
      substrateBinary: process.env.MYCO_SUBSTRATE_BIN,
    },
  });

  // Cleanly shut down the substrate on parent disconnect / SIGINT / SIGTERM.
  const cleanup = async () => {
    try {
      await server.dispose();
    } finally {
      process.exit(0);
    }
  };
  process.on("SIGINT", cleanup);
  process.on("SIGTERM", cleanup);

  await server.start();
}

main().catch((err) => {
  console.error("myco-mcp-claude-code fatal:", err);
  process.exit(1);
});
