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
  // M8 DAG + intent tests (TS-side proof).
  // -------------------------------------------------------------------------
  it("M8: queryRecentNodes returns sporocarp DAG nodes after advance", async () => {
    const client = await spawn();
    try {
      await client.registerAxis({
        name: "dag_test",
        axisClass: "appetite",
        fruitingThreshold: 1.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      // Advance 3 cycles, each producing a sporocarp.
      for (let cycle = 1n; cycle <= 3n; cycle++) {
        await client.perturb("dag_test", 2.0);
        const r = await client.advance(cycle);
        assert.equal(r.sporocarps.length, 1);
      }
      const report = await client.queryRecentNodes(10n);
      assert.equal(report.totalDagSize, 3n);
      assert.equal(report.returnedCount, 3n);
      assert.equal(report.nodes.length, 3);
      assert.ok(report.dagTip !== null);
      // Each node should have node_type starting with "sporocarp:".
      for (const n of report.nodes) {
        assert.match(n.nodeType, /^sporocarp:/);
        assert.equal(n.hash.length, 32);
      }
      // The first node (genesis) has 0 parents; subsequent have 1.
      assert.equal(report.nodes[0]!.parentHashes.length, 0);
      assert.equal(report.nodes[1]!.parentHashes.length, 1);
      assert.equal(report.nodes[2]!.parentHashes.length, 1);
      // Chain integrity: node[1].parent[0] === node[0].hash.
      assert.deepEqual(report.nodes[1]!.parentHashes[0], report.nodes[0]!.hash);
      assert.deepEqual(report.nodes[2]!.parentHashes[0], report.nodes[1]!.hash);
    } finally {
      await client.shutdown();
    }
  });

  it("M8: currentIntent on empty DAG returns cold_start", async () => {
    const client = await spawn();
    try {
      const report = await client.currentIntent({ radiusCycles: 10n });
      assert.equal(report.coldStart, true);
      assert.equal(report.clusterCount, 0n);
      assert.equal(report.clusters.length, 0);
    } finally {
      await client.shutdown();
    }
  });

  it("M8: currentIntent on populated DAG returns clusters", async () => {
    const client = await spawn();
    try {
      await client.registerAxis({
        name: "intent_test",
        axisClass: "appetite",
        fruitingThreshold: 1.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      // Produce 5 sporocarps in a chain.
      for (let cycle = 1n; cycle <= 5n; cycle++) {
        await client.perturb("intent_test", 2.0);
        await client.advance(cycle);
      }
      const report = await client.currentIntent({ radiusCycles: 10n });
      assert.equal(report.coldStart, false);
      // 5 chained sporocarps → 1 connected component (single cluster) when radius is wide enough.
      assert.ok(
        report.clusterCount >= 1n,
        `expected ≥1 cluster on populated DAG; got ${report.clusterCount}`,
      );
      // Total nodes in clusters should account for the DAG.
      const totalInClusters = report.clusters
        .map((c) => c.nodeCount)
        .reduce((a, b) => a + b, 0n);
      assert.ok(
        totalInClusters > 0n,
        `clusters should contain nodes; got ${totalInClusters}`,
      );
    } finally {
      await client.shutdown();
    }
  });

  it("M8: DAG persists across TS-side respawn", async () => {
    const dir = freshStateDir();
    try {
      // Session 1: produce sporocarps.
      const client1 = await spawn(dir);
      await client1.registerAxis({
        name: "persistent_dag",
        axisClass: "appetite",
        fruitingThreshold: 1.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      for (let c = 1n; c <= 3n; c++) {
        await client1.perturb("persistent_dag", 2.0);
        await client1.advance(c);
      }
      const r1 = await client1.queryRecentNodes(10n);
      assert.equal(r1.totalDagSize, 3n);
      const tip1 = r1.dagTip!;
      await client1.shutdown();

      // Session 2: DAG should be hydrated. Advance one more.
      const client2 = await spawn(dir);
      try {
        const r2 = await client2.queryRecentNodes(10n);
        assert.equal(
          r2.totalDagSize,
          3n,
          "DAG should have 3 nodes hydrated from disk",
        );
        assert.deepEqual(
          r2.dagTip,
          tip1,
          "DAG tip should match pre-restart tip",
        );
      } finally {
        await client2.shutdown();
      }
    } finally {
      cleanupDir(dir);
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
