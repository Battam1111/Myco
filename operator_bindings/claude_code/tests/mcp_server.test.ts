// McpServer dispatch tests — go through the MCP tool surface as Claude Code would.
//
// Uses the internal _testDispatch entry point (bypasses the stdio JSON-RPC
// transport) so we can drive the tool surface in-process.

import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { resolve as resolvePath } from "node:path";
import { existsSync } from "node:fs";

import { McpServer } from "../src/mcp_server.ts";

function locateSubstrateBinary(): string {
  const fromEnv = process.env.MYCO_SUBSTRATE_BIN;
  if (fromEnv && existsSync(fromEnv)) return fromEnv;
  const root = resolvePath(import.meta.dirname ?? __dirname, "..", "..", "..");
  const exe = process.platform === "win32" ? ".exe" : "";
  const candidate = resolvePath(root, "target", "debug", `myco-substrate${exe}`);
  if (!existsSync(candidate)) {
    throw new Error(
      `myco-substrate binary not found at ${candidate}; build with: cargo build -p myco-substrate`,
    );
  }
  return candidate;
}

const SUBSTRATE_BIN = locateSubstrateBinary();

function newServer(): McpServer {
  return new McpServer({
    substrate: { substrateBinary: SUBSTRATE_BIN },
  });
}

describe("McpServer tool dispatch", () => {
  it("myco_substrate_info reports versions", async () => {
    const server = newServer();
    try {
      const result = await server._testDispatch("myco_substrate_info", {});
      assert.equal(result.isError, undefined);
      const text = result.content[0]!.text;
      assert.match(text, /substrate_version: 0\.9/);
      assert.match(text, /kernel_tropism_version: 0\.9/);
      assert.match(text, /python_version: \d+\.\d+/);
    } finally {
      await server.dispose();
    }
  });

  it("myco_register_axis + myco_snapshot roundtrip", async () => {
    const server = newServer();
    try {
      const reg = await server._testDispatch("myco_register_axis", {
        name: "kev",
        axis_class: "appetite",
        fruiting_threshold: 3.0,
        initial_value: 0.0,
        decay_rate_per_cycle: 1.0,
        is_mortality_signal: false,
        update_rule_kind: "noop",
      });
      assert.equal(reg.isError, undefined);
      assert.match(reg.content[0]!.text, /Registered axis "kev"/);

      await server._testDispatch("myco_perturb_axis", {
        axis_name: "kev",
        delta: 1.5,
      });
      const snap = await server._testDispatch("myco_snapshot", {});
      assert.equal(snap.isError, undefined);
      assert.match(snap.content[0]!.text, /kev = 1\.5/);
    } finally {
      await server.dispose();
    }
  });

  it("myco_advance_cycle fires sporocarp", async () => {
    const server = newServer();
    try {
      await server._testDispatch("myco_register_axis", {
        name: "fast_appetite",
        axis_class: "appetite",
        fruiting_threshold: 1.0,
        initial_value: 0.0,
        decay_rate_per_cycle: 1.0,
        is_mortality_signal: false,
        update_rule_kind: "noop",
      });
      await server._testDispatch("myco_perturb_axis", {
        axis_name: "fast_appetite",
        delta: 2.0,
      });
      const result = await server._testDispatch("myco_advance_cycle", {
        current_cycle: 1,
      });
      assert.equal(result.isError, undefined);
      const text = result.content[0]!.text;
      assert.match(text, /fruited_axes=\[fast_appetite\]/);
      assert.match(text, /sporocarps=1/);
      assert.match(text, /appetite_fruiting/);
    } finally {
      await server.dispose();
    }
  });

  it("unknown tool returns isError", async () => {
    const server = newServer();
    try {
      const result = await server._testDispatch("nonexistent_tool", {});
      assert.equal(result.isError, true);
      assert.match(result.content[0]!.text, /unknown tool/);
    } finally {
      await server.dispose();
    }
  });

  it("perturb unknown axis returns isError", async () => {
    const server = newServer();
    try {
      const result = await server._testDispatch("myco_perturb_axis", {
        axis_name: "ghost",
        delta: 1.0,
      });
      assert.equal(result.isError, true);
    } finally {
      await server.dispose();
    }
  });

  it("myco_shutdown_substrate works idempotently when not yet spawned", async () => {
    const server = newServer();
    try {
      const result = await server._testDispatch("myco_shutdown_substrate", {});
      assert.equal(result.isError, undefined);
      assert.match(result.content[0]!.text, /not yet spawned/);
    } finally {
      await server.dispose();
    }
  });
});
