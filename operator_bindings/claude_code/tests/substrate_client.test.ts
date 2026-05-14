// SubstrateClient e2e tests — spawn myco-substrate binary, drive full 3-tier stack.
//
// THE M6 milestone proof: TypeScript ↔ Rust ↔ Python with all three
// processes alive, exchanging canonical-bytes frames over stdio.

import { describe, it, after } from "node:test";
import assert from "node:assert/strict";
import { resolve as resolvePath } from "node:path";
import { existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";

import { SubstrateClient } from "../src/substrate_client.ts";

function locateSubstrateBinary(): string {
  const fromEnv = process.env.MYCO_SUBSTRATE_BIN;
  if (fromEnv && existsSync(fromEnv)) return fromEnv;
  // Default: workspace root target/debug/myco-substrate(.exe)
  const root = resolvePath(import.meta.dirname ?? __dirname, "..", "..", "..");
  const exe = process.platform === "win32" ? ".exe" : "";
  const candidate = resolvePath(root, "target", "debug", `myco-substrate${exe}`);
  if (existsSync(candidate)) return candidate;
  throw new Error(
    `myco-substrate binary not found. Build with: cargo build -p myco-substrate (looked at ${candidate})`,
  );
}

const SUBSTRATE_BIN = locateSubstrateBinary();

/** Allocate a fresh isolated state directory for one test. M7: prevents
 *  tests from leaking substrate state into each other or into the user's
 *  default ~/.myco/substrate/default/. */
function freshStateDir(): string {
  return mkdtempSync(resolvePath(tmpdir(), "myco-ts-e2e-"));
}

async function spawn(stateDir?: string): Promise<SubstrateClient> {
  const dir = stateDir ?? freshStateDir();
  return SubstrateClient.spawn({
    substrateBinary: SUBSTRATE_BIN,
    env: { MYCO_STATE_DIR: dir },
  });
}

function cleanupDir(dir: string): void {
  try {
    rmSync(dir, { recursive: true, force: true });
  } catch {
    // Ignore.
  }
}

describe("SubstrateClient e2e", () => {
  it("handshake reports python_version + kernel_tropism_version + substrate_version", async () => {
    const client = await spawn();
    try {
      const ack = client.helloAck;
      assert.ok(ack.pythonVersion.length > 0, "python_version present");
      assert.ok(
        ack.kernelTropismVersion.includes("0.9"),
        `kernel_tropism_version contains 0.9; got ${ack.kernelTropismVersion}`,
      );
      assert.ok(
        ack.substrateVersion.includes("0.9"),
        `substrate_version contains 0.9; got ${ack.substrateVersion}`,
      );
    } finally {
      await client.shutdown();
    }
  });

  it("register + perturb + snapshot roundtrip", async () => {
    const client = await spawn();
    try {
      await client.registerAxis({
        name: "curiosity",
        axisClass: "appetite",
        fruitingThreshold: 10.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      await client.perturb("curiosity", 3.5);
      const snap = await client.snapshot();
      assert.equal(snap.get("curiosity"), 3.5);
    } finally {
      await client.shutdown();
    }
  });

  it("advance fires sporocarp when threshold crossed", async () => {
    const client = await spawn();
    try {
      await client.registerAxis({
        name: "hunger",
        axisClass: "appetite",
        fruitingThreshold: 2.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      await client.perturb("hunger", 3.0); // above threshold
      const report = await client.advance(1n);
      assert.deepEqual(report.fruitedAxes, ["hunger"]);
      assert.equal(report.sporocarps.length, 1);
      const sp = report.sporocarps[0]!;
      assert.equal(sp.sporocarpType, "appetite_fruiting");
      assert.equal(sp.axisName, "hunger");
      assert.equal(sp.atCycle, 1n);
      assert.equal(sp.hash.length, 32);
      assert.ok(sp.canonicalBytes.length > 0);
      // After fruiting, axis resets to initial_value.
      const snap = await client.snapshot();
      assert.equal(snap.get("hunger"), 0.0);
    } finally {
      await client.shutdown();
    }
  });

  it("multiple advances accumulate correctly", async () => {
    const client = await spawn();
    try {
      await client.registerAxis({
        name: "rolling",
        axisClass: "appetite",
        fruitingThreshold: 5.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      let totalSporocarps = 0;
      for (let cycle = 1; cycle <= 8; cycle++) {
        await client.perturb("rolling", 2.0);
        const report = await client.advance(BigInt(cycle));
        totalSporocarps += report.sporocarps.length;
      }
      // 8 cycles × 2.0 fuel each, threshold 5.0 → fruits at cycle 3, 6 → 2 sporocarps
      assert.equal(totalSporocarps, 2);
    } finally {
      await client.shutdown();
    }
  });

  it("decay axis emits mortality sporocarp", async () => {
    const client = await spawn();
    try {
      await client.registerAxis({
        name: "mortality",
        axisClass: "decay",
        fruitingThreshold: 0.1,
        initialValue: 1.0,
        decayRatePerCycle: 0.5,
        isMortalitySignal: true,
        updateRuleKind: "decay",
      });
      let fruitedCycle: bigint | null = null;
      for (let cycle = 1n; cycle <= 10n; cycle++) {
        const report = await client.advance(cycle);
        if (report.fruitedAxes.length > 0) {
          assert.deepEqual(report.fruitedAxes, ["mortality"]);
          assert.equal(
            report.sporocarps[0]!.sporocarpType,
            "mortality_signal_threshold_crossed",
          );
          fruitedCycle = cycle;
          break;
        }
      }
      assert.equal(fruitedCycle, 4n);
    } finally {
      await client.shutdown();
    }
  });

  it("perturb unknown axis returns error", async () => {
    const client = await spawn();
    try {
      await assert.rejects(() => client.perturb("not_registered", 1.0));
    } finally {
      await client.shutdown();
    }
  });

  it("snapshot with no axes returns empty", async () => {
    const client = await spawn();
    try {
      const snap = await client.snapshot();
      assert.equal(snap.size, 0);
    } finally {
      await client.shutdown();
    }
  });

  // -------------------------------------------------------------------------
  // M7 cross-restart test: TS-side proof that substrate state persists across
  // process kill + respawn when the same state_dir is used.
  // -------------------------------------------------------------------------
  it("M7: substrate state survives across TS-side respawn", async () => {
    const dir = freshStateDir();
    try {
      // Session 1: register an axis + perturb, then shutdown.
      const client1 = await spawn(dir);
      await client1.registerAxis({
        name: "ts_survivor",
        axisClass: "appetite",
        fruitingThreshold: 100.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      await client1.perturb("ts_survivor", 3.14);
      await client1.shutdown();

      // Session 2: same dir; verify state was hydrated.
      const client2 = await spawn(dir);
      try {
        const snap = await client2.snapshot();
        assert.equal(
          snap.get("ts_survivor"),
          3.14,
          `ts_survivor=3.14 should survive restart; got snapshot=${JSON.stringify(Array.from(snap))}`,
        );
      } finally {
        await client2.shutdown();
      }
    } finally {
      cleanupDir(dir);
    }
  });
});
