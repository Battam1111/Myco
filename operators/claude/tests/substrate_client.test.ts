// SubstrateClient e2e tests — spawn myco-substrate binary, drive full 3-tier stack.
//
// THE M6 milestone proof: TypeScript ↔ Rust ↔ Python with all three
// processes alive, exchanging canonical-bytes frames over stdio.
//
// **v0.9 owner-key removal**: the handshake is KEYLESS (session_secret only; no
// operator pubkey / hello signature / TOFU pin). All tests that exercised the
// removed owner-key surface — M9 TOFU pinning, M13 attestation nonces, M14
// per-handshake REVEAL keypair, M15 dual-clock nonce expiry, M10/M11 owner
// CI-attestation accept/reject, M-anchor-5 dag_tip_cosign / l0_revision_attest,
// and the M21.1 operator_pinned / nonce_issued / nonce_consumed event emissions —
// were deleted along with that surface. The surviving tests drive the substrate
// keyless: CI-class mutations (schema_evolution / compression /
// owner_objective_declaration) are now classified by the Python classifier on
// mutation_type + content (no signature), and sprout_child sends the
// myco-spawn-cosign-v1 envelope structure without a co-signature.

import { after, describe, it } from "node:test";
import assert from "node:assert/strict";
import { resolve as resolvePath } from "node:path";
import { existsSync, mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";

import { SubstrateClient } from "../src/substrate_client.ts";
import type { FederationStatusResult } from "../src/protocol/messages.ts";

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

// v0.9 keyless: no anchor-surface-host binary, no operator-identity env. The
// handshake completes on session_secret alone. This `after` hook is retained
// as a no-op placeholder so the suite shape is stable; there are no
// anchor-surface child processes to reap anymore.
after(async () => {
  // nothing to tear down (keyless).
});

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

/** **P08 §3.5 / §5.1** (KEYLESS v0.9) — build a minimal-but-well-formed child
 *  spore-schema (the 7-field L1/SCHEMA §3.1 shape) for the sprout path. The
 *  substrate validates the SHAPE + the blake3 binding to the spawn-cosign
 *  envelope (not a signature), so any non-Null value per field suffices. The
 *  `anchor_surface_config` descriptor field is a 32-zero-byte marker (no owner
 *  pubkey exists in v0.9). */
async function buildTestSporeSchemaBytes(): Promise<Uint8Array> {
  const { buildSporeSchemaCanonicalBytes } = await import(
    "../src/protocol/messages.ts"
  );
  return buildSporeSchemaCanonicalBytes({
    schemaDefinitions: { type: "string", value: "child-schema-v1" },
    canonicalBytesSerializerSpec: {
      type: "string",
      value: "myco-canonical-bytes-v1",
    },
    sporocarpTypeTree: { type: "string", value: "myco-sporocarp-tree-v1" },
    classifierDimensionTable: { type: "string", value: "myco-classifier-v1" },
    initialAppetiteAxisSchema: { type: "string", value: "axes-v1" },
    anchorSurfaceConfig: { type: "bytes", value: new Uint8Array(32) },
    parentImmuneSignalSummary: {
      type: "map",
      value: new Map([["unresolved_count", { type: "uint", value: 0n }]]),
    },
  });
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
      assert.ok(ack.substrateVersion.length > 0, "substrate_version present");
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
  // M12 integrity-scan tests.
  // -------------------------------------------------------------------------
  it("M12: runImmuneCheck on healthy substrate returns all checks passed", async () => {
    const client = await spawn();
    try {
      const report = await client.runImmuneCheck();
      assert.ok(
        report.totalChecks >= 4n,
        `expected ≥4 checks; got ${report.totalChecks}`,
      );
      assert.equal(report.failedChecks, 0n);
      assert.equal(report.immuneEventsEmitted, 0n);
      // All individual checks should report passed=true.
      for (const check of report.checks) {
        assert.equal(
          check.passed,
          true,
          `${check.checkId} should pass on healthy substrate; got: ${check.evidence}`,
        );
      }
    } finally {
      await client.shutdown();
    }
  });

  it("M12: runImmuneCheck includes substrate_id + dag + core integrity checks", async () => {
    const client = await spawn();
    try {
      const report = await client.runImmuneCheck();
      const checkIds = report.checks.map((c) => c.checkId);
      assert.ok(checkIds.includes("substrate_id_well_formed"));
      assert.ok(checkIds.includes("cycle_counter_monotonic"));
      assert.ok(checkIds.includes("dag_verify_all"));
      // v0.9 owner-key removal: the `pinned_pubkey_well_formed` check (M9 TOFU
      // operator-pubkey pin) was removed with the anchor surface. The remaining
      // C9-family checks (incl. canonical_bytes_render_drift, orphan, genesis
      // uniqueness) survive keyless.
      assert.ok(checkIds.includes("canonical_bytes_render_drift"));
      assert.ok(checkIds.includes("substrate_state_orphan_detected"));
    } finally {
      await client.shutdown();
    }
  });

  it("M12: runImmuneCheck does NOT add immune events when all checks pass", async () => {
    const client = await spawn();
    try {
      const before = await client.queryImmuneEvents();
      await client.runImmuneCheck();
      const after = await client.queryImmuneEvents();
      assert.equal(
        after.totalImmuneCount,
        before.totalImmuneCount,
        "no immune events should be emitted on a healthy substrate",
      );
    } finally {
      await client.shutdown();
    }
  });

  it("M12: tampered DAG triggers C7 + multiple C9 checks at boot", async () => {
    const dir = freshStateDir();
    try {
      // Session 1: produce some DAG content.
      const c1 = await spawn(dir);
      await c1.submitMutation({
        mutationType: "delta_absorb",
        contentCanonicalBytes: new TextEncoder().encode("setup content"),
      });
      await c1.shutdown();

      // Tamper: corrupt dag.cb on disk.
      const { writeFileSync } = await import("node:fs");
      const dagPath = resolvePath(dir, "dag.cb");
      writeFileSync(dagPath, new Uint8Array([0xff, 0xff, 0xff, 0xff, 0xff, 0xff]));

      // Session 2: substrate detects + recovers + emits C7.
      const c2 = await spawn(dir);
      try {
        const events = await c2.queryImmuneEvents();
        assert.ok(
          events.totalImmuneCount >= 1n,
          `expected at least 1 immune event after tamper; got ${events.totalImmuneCount}`,
        );
        const c7Event = events.events.find((e) =>
          e.nodeType.includes("C7_dag_retro_edit_detected"),
        );
        assert.ok(c7Event, "C7 detector should fire on dag.cb tamper");
      } finally {
        await c2.shutdown();
      }
    } finally {
      cleanupDir(dir);
    }
  });

  // -------------------------------------------------------------------------
  // M11 active immune system tests (keyless survivors).
  // -------------------------------------------------------------------------
  it("M11: empty substrate has no immune events", async () => {
    const client = await spawn();
    try {
      const report = await client.queryImmuneEvents();
      assert.equal(report.totalImmuneCount, 0n);
      assert.equal(report.returnedCount, 0n);
      assert.equal(report.events.length, 0);
    } finally {
      await client.shutdown();
    }
  });

  it("M11: UNTYPED mutation emits C14 immune sporocarp", async () => {
    const client = await spawn();
    try {
      const result = await client.submitMutation({
        mutationType: "completely_unknown_xyz",
        contentCanonicalBytes: new TextEncoder().encode("attack"),
      });
      assert.equal(result.accepted, false);
      assert.equal(result.classification, "untyped");
      // Check immune event was emitted.
      const report = await client.queryImmuneEvents();
      assert.equal(report.totalImmuneCount, 1n);
      assert.equal(report.events.length, 1);
      assert.equal(
        report.events[0]!.nodeType,
        "immune:C14_untyped_mutation_blocked",
      );
    } finally {
      await client.shutdown();
    }
  });

  it("M11: immune events persist across restart", async () => {
    const dir = freshStateDir();
    try {
      const c1 = await spawn(dir);
      // Emit a C14 immune event.
      await c1.submitMutation({
        mutationType: "untyped_xyz_persist",
        contentCanonicalBytes: new TextEncoder().encode("attack"),
      });
      const before = await c1.queryImmuneEvents();
      assert.ok(before.totalImmuneCount >= 1n);
      await c1.shutdown();

      const c2 = await spawn(dir);
      try {
        const after = await c2.queryImmuneEvents();
        assert.ok(
          after.totalImmuneCount >= 1n,
          "immune events should survive restart via dag.cb",
        );
        const c14 = after.events.find((e) =>
          e.nodeType.includes("C14_untyped_mutation_blocked"),
        );
        assert.ok(c14, "the C14 event should be present after restart");
      } finally {
        await c2.shutdown();
      }
    } finally {
      cleanupDir(dir);
    }
  });

  // -------------------------------------------------------------------------
  // M10 classified-mutation tests (keyless survivors). The owner CI-attestation
  // accept/reject tests were removed with the anchor surface.
  // -------------------------------------------------------------------------
  it("M10: DAILY mutation is accepted and recorded as DAG node", async () => {
    const client = await spawn();
    try {
      const result = await client.submitMutation({
        mutationType: "delta_absorb",
        contentCanonicalBytes: new TextEncoder().encode("daily content"),
      });
      assert.equal(result.accepted, true);
      assert.equal(result.classification, "daily");
      // The mutation lands as a mutation:* DAG node.
      const recent = await client.queryRecentNodes(20n, "mutation:");
      assert.ok(
        recent.filteredTotal >= 1n,
        "accepted daily mutation must land as a mutation:* DAG node",
      );
    } finally {
      await client.shutdown();
    }
  });

  it("M10: UNTYPED mutation is rejected (L1/HARD_RULES C14)", async () => {
    const client = await spawn();
    try {
      const result = await client.submitMutation({
        mutationType: "this_is_not_a_known_type",
        contentCanonicalBytes: new TextEncoder().encode("x"),
      });
      assert.equal(result.accepted, false);
      assert.equal(result.classification, "untyped");
    } finally {
      await client.shutdown();
    }
  });

  it("M10: accepted DAILY mutation DAG persists across restart", async () => {
    const dir = freshStateDir();
    try {
      const c1 = await spawn(dir);
      await c1.submitMutation({
        mutationType: "delta_absorb",
        contentCanonicalBytes: new TextEncoder().encode("persist daily"),
      });
      const pre = await c1.queryRecentNodes(20n, "mutation:");
      assert.ok(pre.filteredTotal >= 1n);
      await c1.shutdown();

      const c2 = await spawn(dir);
      try {
        const post = await c2.queryRecentNodes(20n, "mutation:");
        assert.ok(
          post.filteredTotal >= 1n,
          "accepted daily mutation DAG node should survive restart",
        );
      } finally {
        await c2.shutdown();
      }
    } finally {
      cleanupDir(dir);
    }
  });

  // -------------------------------------------------------------------------
  // M8 DAG diagnostics + intent.
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
      // M21.1: filter for sporocarp:* to isolate the 3 fruiting events from
      // the (many) init / cycle_advanced / axis_perturbed events also in DAG.
      const sporocarps = await client.queryRecentNodes(10n, "sporocarp:");
      assert.equal(sporocarps.filteredTotal, 3n);
      assert.equal(sporocarps.returnedCount, 3n);
      assert.equal(sporocarps.nodes.length, 3);
      for (const n of sporocarps.nodes) {
        assert.match(n.nodeType, /^sporocarp:/);
        assert.equal(n.hash.length, 32);
      }
    } finally {
      await client.shutdown();
    }
  });

  it("M8: currentIntent on substrate with no operational events returns small/empty intent", async () => {
    const client = await spawn();
    try {
      // M21.1 dual-write: even a "fresh" substrate has a genesis_event in the
      // DAG. coldStart is therefore false, but there are no SPOROCARP or
      // MUTATION events to cluster around — the intent neighborhood is just
      // init events (typically 1-2 nodes, no meaningful clusters).
      const report = await client.currentIntent({ radiusCycles: 10n });
      // The intent is trivially "fresh substrate" — at most 1 cluster of init events.
      assert.ok(
        report.clusterCount <= 1n,
        `expected ≤1 cluster on near-empty substrate; got ${report.clusterCount}`,
      );
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
      // M21.1: count sporocarp:* events specifically; init events also in DAG.
      const sp1 = await client1.queryRecentNodes(10n, "sporocarp:");
      assert.equal(sp1.filteredTotal, 3n);
      const fullPre = await client1.queryRecentNodes(50n);
      const totalDagPre = fullPre.totalDagSize;
      const tip1 = fullPre.dagTip!;
      await client1.shutdown();

      // Session 2: DAG should be hydrated. Advance one more.
      const client2 = await spawn(dir);
      try {
        const sp2 = await client2.queryRecentNodes(10n, "sporocarp:");
        assert.equal(
          sp2.filteredTotal,
          3n,
          "3 sporocarp events should survive restart",
        );
        const fullPost = await client2.queryRecentNodes(50n);
        // **M-anchor-4 §9.3.4**: every boot emits `invariant_witness:*` events
        // for tier-1 integrity checks (per-cycle witness emission with cycle
        // dedup). Count ONLY the persistent (pre-M-anchor-4) event types to
        // assert identical-content-survives-restart semantics.
        const witnessCountPost = fullPost.nodes.filter((n) =>
          n.nodeType.startsWith("invariant_witness:"),
        ).length;
        const witnessCountPre = fullPre.nodes.filter((n) =>
          n.nodeType.startsWith("invariant_witness:"),
        ).length;
        const stableSizePre = Number(totalDagPre) - witnessCountPre;
        const stableSizePost = Number(fullPost.totalDagSize) - witnessCountPost;
        assert.equal(
          stableSizePost,
          stableSizePre,
          `non-witness DAG size should survive restart; pre=${stableSizePre}, post=${stableSizePost}, totalPre=${totalDagPre}, totalPost=${fullPost.totalDagSize}`,
        );
        void tip1;
      } finally {
        await client2.shutdown();
      }
    } finally {
      cleanupDir(dir);
    }
  });

  // -------------------------------------------------------------------------
  // M7 cross-restart test.
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

  // -------------------------------------------------------------------------
  // M15 DAG enumeration closure (the dual-clock nonce tests were removed with
  // the anchor surface; the keyless enumeration + BLAKE3-chain verify remain).
  // -------------------------------------------------------------------------

  it("M15: enumerateDagSince(undefined) returns all nodes from genesis", async () => {
    const client = await spawn();
    try {
      await client.registerAxis({
        name: "enum_axis",
        axisClass: "appetite",
        fruitingThreshold: 1.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      // Produce 3 sporocarp nodes.
      for (let c = 1n; c <= 3n; c++) {
        await client.perturb("enum_axis", 2.0);
        await client.advance(c);
      }
      const report = await client.enumerateDagSince();
      assert.ok(
        report.totalDagSize >= 3n,
        `expected at least 3 nodes; got ${report.totalDagSize}`,
      );
      assert.equal(report.enumeratedCount, report.totalDagSize);
      assert.equal(report.prevTip, null, "from-genesis enumeration should echo null prev_tip");
      assert.ok(report.currentTip !== null, "current_tip should be set");
      // The BLAKE3 chain verification must pass on the full enumeration.
      const errors = await SubstrateClient.verifyEnumeration(report);
      assert.deepEqual(errors, [], `expected hash chain verification to pass; got: ${errors.join(" | ")}`);
      // Sanity: 3 sporocarp nodes should be among them.
      const sporocarpCount = report.nodes.filter((n) =>
        n.nodeType.startsWith("sporocarp:"),
      ).length;
      assert.equal(sporocarpCount, 3);
    } finally {
      await client.shutdown();
    }
  });

  it("M15: enumerateDagSince(intermediate_tip) returns only nodes after", async () => {
    const client = await spawn();
    try {
      await client.registerAxis({
        name: "enum_axis2",
        axisClass: "appetite",
        fruitingThreshold: 1.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      // Insert 2 sporocarps; snapshot tip; insert 2 more.
      for (let c = 1n; c <= 2n; c++) {
        await client.perturb("enum_axis2", 2.0);
        await client.advance(c);
      }
      const tipAtTwoCycles = (await client.queryRecentNodes(1n)).dagTip!;
      const totalAtTwoCycles = (await client.queryRecentNodes(1n)).totalDagSize;
      for (let c = 3n; c <= 4n; c++) {
        await client.perturb("enum_axis2", 2.0);
        await client.advance(c);
      }
      const finalTotal = (await client.queryRecentNodes(1n)).totalDagSize;
      const report = await client.enumerateDagSince(tipAtTwoCycles);
      assert.equal(report.totalDagSize, finalTotal);
      // enumeratedCount = nodes added since tipAtTwoCycles
      const expectedEnum = finalTotal - totalAtTwoCycles;
      assert.equal(
        report.enumeratedCount,
        expectedEnum,
        `should enumerate ${expectedEnum} nodes added after the snapshot tip`,
      );
      // The first enumerated node has tipAtTwoCycles as a parent.
      if (report.nodes.length > 0) {
        assert.deepEqual(report.nodes[0]!.parentHashes[0], tipAtTwoCycles);
      }
    } finally {
      await client.shutdown();
    }
  });

  it("M15: enumerateDagSince(unknown_tip) is rejected + emits C6 immune", async () => {
    const client = await spawn();
    try {
      // Produce some nodes so the DAG is non-empty.
      await client.registerAxis({
        name: "enum_axis3",
        axisClass: "appetite",
        fruitingThreshold: 1.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      await client.perturb("enum_axis3", 2.0);
      await client.advance(1n);

      const fakeTip = new Uint8Array(32).fill(0xfe);
      await assert.rejects(
        () => client.enumerateDagSince(fakeTip),
        /enumerate_dag_since|unknown|dispatcher_error/,
      );
      // C6 immune sporocarp should be emitted.
      const events = await client.queryImmuneEvents();
      const c6 = events.events.find((e) =>
        e.nodeType.includes("C6_dag_enumeration_unclosed"),
      );
      assert.ok(c6, "expected C6 immune sporocarp on unknown prev_tip");
    } finally {
      await client.shutdown();
    }
  });

  it("M15: BLAKE3 chain reconstruction detects substrate hash forgery (synthetic)", async () => {
    // Build a synthetic enumeration with one node whose claimed hash does
    // NOT match its parents+content. verifyEnumeration must catch this.
    const goodNode = {
      hash: new Uint8Array(32).fill(0x11),
      parentHashes: [],
      nodeType: "genesis",
      atCycle: 0n,
      contentCanonicalBytes: new Uint8Array([0x01, 0x02, 0x03]),
    };
    const forgedReport = {
      currentTip: goodNode.hash,
      prevTip: null,
      totalDagSize: 1n,
      enumeratedCount: 1n,
      nodes: [goodNode],
    };
    const errors = await SubstrateClient.verifyEnumeration(forgedReport);
    assert.ok(errors.length > 0, "synthetic hash-mismatch should be caught");
    assert.match(errors[0]!, /hash mismatch/);
  });

  // -------------------------------------------------------------------------
  // M16 P2 永恒吞噬 ingest + causal-link tests.
  // -------------------------------------------------------------------------
  it("M16: ingest text raw_material grows DAG by 1 raw_material:text node", async () => {
    const client = await spawn();
    try {
      const content = new TextEncoder().encode("a poem about mycelium");
      const result = await client.ingestRawMaterial({
        contentKind: "text",
        contentBytes: content,
        sourceUri: "poem.txt",
      });
      assert.equal(result.dagNodeHash.length, 32);
      // M21.1: total DAG size includes init events; raw_material count is what we check.
      assert.ok(result.totalDagSize >= 1n);

      // The node is queryable via raw_material: prefix filter.
      const report = await client.queryRecentNodes(10n, "raw_material:");
      assert.equal(report.filteredTotal, 1n);
      assert.equal(report.nodes.length, 1);
      assert.equal(report.nodes[0]!.nodeType, "raw_material:text");
      assert.deepEqual(report.nodes[0]!.hash, result.dagNodeHash);
    } finally {
      await client.shutdown();
    }
  });

  it("M16: ingest of multiple kinds preserves all with proper node_types", async () => {
    const client = await spawn();
    try {
      const kinds: Array<{ k: string; b: Uint8Array }> = [
        { k: "text", b: new TextEncoder().encode("plain text") },
        { k: "conversation", b: new TextEncoder().encode("user said hello") },
        { k: "url", b: new TextEncoder().encode("https://example.org/page") },
        { k: "llm_response", b: new TextEncoder().encode("LLM output here") },
        { k: "file", b: new TextEncoder().encode("file contents") },
      ];
      for (const item of kinds) {
        await client.ingestRawMaterial({
          contentKind: item.k,
          contentBytes: item.b,
        });
      }
      const report = await client.queryRecentNodes(20n, "raw_material:");
      assert.equal(report.filteredTotal, 5n);
      const nodeTypes = report.nodes.map((n) => n.nodeType).sort();
      assert.deepEqual(nodeTypes, [
        "raw_material:conversation",
        "raw_material:file",
        "raw_material:llm_response",
        "raw_material:text",
        "raw_material:url",
      ]);
    } finally {
      await client.shutdown();
    }
  });

  it("M16: ingestion exceeding 512 KiB content cap is rejected with explicit error", async () => {
    const client = await spawn();
    try {
      const tooBig = new Uint8Array(512 * 1024 + 1); // 512 KiB + 1 byte
      tooBig.fill(0x41);
      await assert.rejects(
        () =>
          client.ingestRawMaterial({
            contentKind: "text",
            contentBytes: tooBig,
          }),
        /exceeds.*cap|byte cap/i,
      );
    } finally {
      await client.shutdown();
    }
  });

  it("M16: ingestion at exactly the 512 KiB cap is accepted", async () => {
    const client = await spawn();
    try {
      const atCap = new Uint8Array(512 * 1024); // exactly 512 KiB
      atCap.fill(0x42);
      const result = await client.ingestRawMaterial({
        contentKind: "text",
        contentBytes: atCap,
      });
      assert.equal(result.dagNodeHash.length, 32);
    } finally {
      await client.shutdown();
    }
  });

  it("M16: perturbAxisFromRawMaterial creates causal link with both parents", async () => {
    const client = await spawn();
    try {
      // First register the axis we'll perturb.
      await client.registerAxis({
        name: "curiosity",
        axisClass: "appetite",
        fruitingThreshold: 100.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      // Ingest some raw material.
      const content = new TextEncoder().encode("an interesting paper abstract");
      const ingest = await client.ingestRawMaterial({
        contentKind: "text",
        contentBytes: content,
        sourceUri: "https://arxiv.org/abs/example",
      });
      // Perturb from raw material.
      const link = await client.perturbAxisFromRawMaterial({
        axisName: "curiosity",
        delta: 5.0,
        rawMaterialHash: ingest.dagNodeHash,
      });
      assert.equal(link.causalLinkHash.length, 32);
      assert.deepEqual(link.rawMaterialHash, ingest.dagNodeHash);
      // M21.1: filter by perturb_from_raw: to find the causal link node.
      const links = await client.queryRecentNodes(20n, "perturb_from_raw:");
      assert.equal(links.filteredTotal, 1n);
      const linkNode = links.nodes[0]!;
      assert.match(linkNode.nodeType, /^perturb_from_raw:curiosity$/);
      // The link node has parents including the raw_material hash.
      assert.ok(
        linkNode.parentHashes.length >= 1,
        "perturb_from_raw should have at least 1 parent",
      );
      // Verify the perturbation actually applied — snapshot the gradient.
      const snap = await client.snapshot();
      assert.equal(snap.get("curiosity"), 5.0);
    } finally {
      await client.shutdown();
    }
  });

  it("M16: perturbAxisFromRawMaterial rejects unknown raw_material hash", async () => {
    const client = await spawn();
    try {
      await client.registerAxis({
        name: "test_axis",
        axisClass: "appetite",
        fruitingThreshold: 10.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      const fakeHash = new Uint8Array(32).fill(0xab);
      await assert.rejects(
        () =>
          client.perturbAxisFromRawMaterial({
            axisName: "test_axis",
            delta: 1.0,
            rawMaterialHash: fakeHash,
          }),
        /not found|unknown|raw_material_hash/i,
      );
    } finally {
      await client.shutdown();
    }
  });

  it("M16: perturbAxisFromRawMaterial rejects hash that points to non-raw_material node", async () => {
    const client = await spawn();
    try {
      await client.registerAxis({
        name: "ax",
        axisClass: "appetite",
        fruitingThreshold: 1.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      // Produce a sporocarp node (not a raw_material node).
      await client.perturb("ax", 2.0);
      const advReport = await client.advance(1n);
      const sporocarpHash = advReport.sporocarps[0]!.canonicalBytes; // wrong type
      const recent = await client.queryRecentNodes(5n);
      const sporocarp = recent.nodes.find((n) =>
        n.nodeType.startsWith("sporocarp:"),
      );
      assert.ok(sporocarp);
      void sporocarpHash;
      await assert.rejects(
        () =>
          client.perturbAxisFromRawMaterial({
            axisName: "ax",
            delta: 1.0,
            rawMaterialHash: sporocarp!.hash,
          }),
        /not raw_material|raw_material/i,
      );
    } finally {
      await client.shutdown();
    }
  });

  it("M16: ingested raw_material persists across substrate restart", async () => {
    const dir = freshStateDir();
    try {
      const c1 = await spawn(dir);
      const content = new TextEncoder().encode("persistent meal");
      await c1.ingestRawMaterial({
        contentKind: "text",
        contentBytes: content,
      });
      await c1.shutdown();

      const c2 = await spawn(dir);
      try {
        const report = await c2.queryRecentNodes(10n, "raw_material:");
        assert.equal(
          report.filteredTotal,
          1n,
          "ingested raw_material should survive restart via dag.cb",
        );
        assert.equal(report.nodes[0]!.nodeType, "raw_material:text");
      } finally {
        await c2.shutdown();
      }
    } finally {
      cleanupDir(dir);
    }
  });

  it("M16: queryRecentNodes prefix filter exposes filteredTotal vs totalDagSize", async () => {
    const client = await spawn();
    try {
      await client.ingestRawMaterial({
        contentKind: "text",
        contentBytes: new TextEncoder().encode("one"),
      });
      await client.ingestRawMaterial({
        contentKind: "text",
        contentBytes: new TextEncoder().encode("two"),
      });
      const filtered = await client.queryRecentNodes(50n, "raw_material:");
      const all = await client.queryRecentNodes(50n);
      assert.equal(filtered.filteredTotal, 2n);
      assert.ok(
        all.totalDagSize > filtered.filteredTotal,
        "total DAG size includes init events beyond the filtered raw_material nodes",
      );
    } finally {
      await client.shutdown();
    }
  });

  // -------------------------------------------------------------------------
  // M17 P3 永恒进化: schema_evolution actually-applied tests (KEYLESS v0.9 —
  // the owner Ed25519 attestation gate was removed; the substrate classifies +
  // applies the schema_evolution on mutation_type + content).
  // -------------------------------------------------------------------------

  it("M17: modify_axis_threshold actually changes the threshold + emits evolution_succeeded", async () => {
    const client = await spawn();
    try {
      const { schemaDiffModifyAxisThresholdBytes } = await import(
        "../src/protocol/messages.ts"
      );
      // Register an axis at threshold 10.0.
      await client.registerAxis({
        name: "curiosity",
        axisClass: "appetite",
        fruitingThreshold: 10.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });

      // Evolve: change threshold to 50.0 (keyless — no attestation).
      const diff = schemaDiffModifyAxisThresholdBytes("curiosity", 50.0);
      const result = await client.submitMutation({
        mutationType: "schema_evolution",
        contentCanonicalBytes: diff,
        touchedMetaStructures: ["appetite_axis_schema"],
      });
      assert.equal(result.accepted, true, `accepted; got: ${result.rejectionReason}`);
      assert.equal(result.schemaApplyAttempted, true);
      assert.equal(result.schemaApplySucceeded, true, result.schemaApplyFailureReason);
      assert.equal(result.schemaApplyOp, "modify_axis_threshold");
      assert.ok(result.evolutionEventHash, "evolution_event_hash should be set");

      // DAG should contain mutation:schema_evolution + evolution_succeeded:modify_axis_threshold.
      const recent = await client.queryRecentNodes(10n);
      const evoSucceeded = recent.nodes.find((n) =>
        n.nodeType.startsWith("evolution_succeeded:"),
      );
      assert.ok(evoSucceeded, "expected evolution_succeeded:* DAG node");
      const mutationNode = recent.nodes.find((n) =>
        n.nodeType === "mutation:schema_evolution",
      );
      assert.ok(mutationNode, "expected mutation:schema_evolution DAG node");

      // Threshold actually changed: perturb just past old threshold, advance.
      await client.perturb("curiosity", 15.0);
      const adv = await client.advance(1n);
      assert.deepEqual(
        adv.fruitedAxes,
        [],
        "axis should NOT fruit at value=15 if new threshold is 50",
      );
    } finally {
      await client.shutdown();
    }
  });

  it("M17: modify_axis_threshold on unknown axis emits evolution_failed + rolls back", async () => {
    const client = await spawn();
    try {
      const { schemaDiffModifyAxisThresholdBytes } = await import(
        "../src/protocol/messages.ts"
      );
      const diff = schemaDiffModifyAxisThresholdBytes("nonexistent_axis", 99.0);
      const result = await client.submitMutation({
        mutationType: "schema_evolution",
        contentCanonicalBytes: diff,
        touchedMetaStructures: ["appetite_axis_schema"],
      });
      // Mutation is still "accepted" (the proposal was valid + well-typed).
      assert.equal(result.accepted, true);
      // But the schema apply FAILED → rollback path.
      assert.equal(result.schemaApplyAttempted, true);
      assert.equal(result.schemaApplySucceeded, false);
      assert.match(result.schemaApplyFailureReason, /AxisNotFound|nonexistent/i);

      // DAG should contain mutation:schema_evolution + evolution_failed:*.
      const recent = await client.queryRecentNodes(10n);
      const evoFailed = recent.nodes.find((n) =>
        n.nodeType.startsWith("evolution_failed:"),
      );
      assert.ok(evoFailed, "expected evolution_failed:* DAG node");
    } finally {
      await client.shutdown();
    }
  });

  it("M17: add_axis_to_gradient registers axis via the schema gate + emits evolution_succeeded", async () => {
    const client = await spawn();
    try {
      const { schemaDiffAddAxisBytes } = await import(
        "../src/protocol/messages.ts"
      );
      const diff = schemaDiffAddAxisBytes({
        axisName: "newly_evolved",
        axisClass: "appetite",
        fruitingThreshold: 4.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      const result = await client.submitMutation({
        mutationType: "schema_evolution",
        contentCanonicalBytes: diff,
        touchedMetaStructures: ["appetite_axis_schema"],
      });
      assert.equal(result.accepted, true, `accepted; got: ${result.rejectionReason}`);
      assert.equal(result.schemaApplySucceeded, true, result.schemaApplyFailureReason);
      assert.equal(result.schemaApplyOp, "add_axis_to_gradient");

      // The new axis is now live: perturb past its threshold + advance → fruit.
      await client.perturb("newly_evolved", 5.0);
      const adv = await client.advance(1n);
      assert.deepEqual(adv.fruitedAxes, ["newly_evolved"]);
    } finally {
      await client.shutdown();
    }
  });

  // -------------------------------------------------------------------------
  // M18 raw_material absorption tests.
  // -------------------------------------------------------------------------
  it("M18: advance with no raw_material absorbs zero deltas (no absorption_event)", async () => {
    const client = await spawn();
    try {
      await client.advance(1n);
      const events = await client.queryRecentNodes(20n, "absorption_event:");
      assert.equal(events.filteredTotal, 0n);
    } finally {
      await client.shutdown();
    }
  });

  it("M18: advance after ingesting raw_material emits absorption_event:cycle_{N}", async () => {
    const client = await spawn();
    try {
      await client.ingestRawMaterial({
        contentKind: "text",
        contentBytes: new TextEncoder().encode("absorb me"),
      });
      await client.advance(1n);
      const events = await client.queryRecentNodes(20n, "absorption_event:");
      assert.ok(
        events.filteredTotal >= 1n,
        `expected ≥1 absorption_event after ingest+advance; got ${events.filteredTotal}`,
      );
    } finally {
      await client.shutdown();
    }
  });

  it("M18: subsequent advances skip already-absorbed raw_material", async () => {
    const client = await spawn();
    try {
      await client.ingestRawMaterial({
        contentKind: "text",
        contentBytes: new TextEncoder().encode("absorb once"),
      });
      await client.advance(1n);
      const after1 = await client.queryRecentNodes(50n, "absorption_event:");
      const count1 = after1.filteredTotal;
      // Second advance with no new raw_material → no new absorption_event.
      await client.advance(2n);
      const after2 = await client.queryRecentNodes(50n, "absorption_event:");
      assert.equal(
        after2.filteredTotal,
        count1,
        "no new absorption_event when there is no fresh raw_material",
      );
    } finally {
      await client.shutdown();
    }
  });

  it("M18: advance with no axes registered still completes (Tier1 DAG verify passes)", async () => {
    const client = await spawn();
    try {
      const adv = await client.advance(1n);
      assert.equal(adv.fruitedAxes.length, 0);
      const integrity = await client.runImmuneCheck();
      assert.equal(integrity.failedChecks, 0n);
    } finally {
      await client.shutdown();
    }
  });

  it("M18: absorption_event has multi-parent linkage (prior_tip + raw_material hashes)", async () => {
    const client = await spawn();
    try {
      const ing = await client.ingestRawMaterial({
        contentKind: "text",
        contentBytes: new TextEncoder().encode("multi-parent absorb"),
      });
      await client.advance(1n);
      const events = await client.queryRecentNodes(20n, "absorption_event:");
      assert.ok(events.filteredTotal >= 1n);
      const node = events.nodes[0]!;
      // The absorption_event references the raw_material hash among its parents.
      const referencesRaw = node.parentHashes.some(
        (p) =>
          p.length === ing.dagNodeHash.length &&
          p.every((b, i) => b === ing.dagNodeHash[i]),
      );
      assert.ok(
        node.parentHashes.length >= 1 || referencesRaw,
        "absorption_event should have causal-parent linkage",
      );
    } finally {
      await client.shutdown();
    }
  });

  it("M18: last_absorbed_cycle persists across substrate restart", async () => {
    const dir = freshStateDir();
    try {
      const c1 = await spawn(dir);
      await c1.ingestRawMaterial({
        contentKind: "text",
        contentBytes: new TextEncoder().encode("absorb-then-restart"),
      });
      await c1.advance(1n);
      const pre = await c1.queryRecentNodes(50n, "absorption_event:");
      assert.ok(pre.filteredTotal >= 1n);
      await c1.shutdown();

      const c2 = await spawn(dir);
      try {
        // After restart, absorbing again with no fresh material should not
        // re-absorb the already-absorbed material.
        await c2.advance(2n);
        const post = await c2.queryRecentNodes(50n, "absorption_event:");
        assert.equal(
          post.filteredTotal,
          pre.filteredTotal,
          "last_absorbed_cycle should survive restart (no re-absorption)",
        );
      } finally {
        await c2.shutdown();
      }
    } finally {
      cleanupDir(dir);
    }
  });

  // -------------------------------------------------------------------------
  // M20 P8 永恒繁衍: sprout_child (KEYLESS v0.9 — the substrate still requires
  // the myco-spawn-cosign-v1 envelope STRUCTURE + I7(a) spore-schema binding,
  // but no co-signature; C68 still fires on a missing/malformed envelope).
  // -------------------------------------------------------------------------

  it("M20 P8 + P08 §3.5: sproutChild creates child dag + spore_emission + genesis_attested", async () => {
    const parentDir = freshStateDir();
    const childDir = mkdtempSync(resolvePath(tmpdir(), "myco-m20-child-"));
    // Pre-remove so substrate creates fresh.
    rmSync(childDir, { recursive: true, force: true });
    try {
      const client = await spawn(parentDir);
      try {
        // Register an axis on the parent.
        await client.registerAxis({
          name: "curiosity",
          axisClass: "appetite",
          fruitingThreshold: 10.0,
          initialValue: 3.0,
          decayRatePerCycle: 1.0,
          isMortalitySignal: false,
          updateRuleKind: "noop",
        });

        const sporeSchemaCanonicalBytes = await buildTestSporeSchemaBytes();
        const result = await client.sproutChild({
          childStateDir: childDir,
          sporeSchemaCanonicalBytes,
        });
        assert.equal(result.childSubstrateId.length, 32);
        assert.equal(result.childStateDir, childDir);
        assert.equal(result.childAxisCount, 1n);
        assert.equal(result.sporeEmissionHash.length, 32);
        // P08 §3.5: the I7-closure record hash is returned.
        assert.equal(result.genesisAttestedHash.length, 32);
        assert.ok(
          result.childGenesisTimestampUnixNs > 0n,
          "child genesis timestamp present",
        );

        // M21.4: child's state_dir contains dag.cb (+ substrate-private signing
        // key). Identity, gradient, etc. are all encoded as events in the DAG.
        assert.ok(existsSync(`${childDir}/dag.cb`), "child dag.cb exists");
        // Legacy state files MUST NOT be created.
        assert.ok(
          !existsSync(`${childDir}/manifest.cb`),
          "post-M21.4: child must NOT have legacy manifest.cb",
        );
        assert.ok(
          !existsSync(`${childDir}/gradient.cb`),
          "post-M21.4: child must NOT have legacy gradient.cb",
        );

        // Verify parent's DAG has the spore_emission node.
        const recent = await client.queryRecentNodes(10n, "spore_emission:");
        assert.equal(recent.filteredTotal, 1n);
        // P08 §3.5: parent's DAG has the genesis_attested I7-closure node.
        const attested = await client.queryRecentNodes(10n, "genesis_attested:");
        assert.equal(
          attested.filteredTotal,
          1n,
          "parent must emit exactly one genesis_attested:* node",
        );
      } finally {
        await client.shutdown();
      }
    } finally {
      cleanupDir(parentDir);
      cleanupDir(childDir);
    }
  });

  it("P08 §5.1: sproutChild with NO spawn-cosign envelope is refused with C68", async () => {
    // A bare sprout_child request WITHOUT the myco-spawn-cosign-v1 envelope must
    // be refused before any side effect (the envelope STRUCTURE is the keyless
    // CI-class gate; only the Ed25519 co-signature was removed).
    const parentDir = freshStateDir();
    const childDir = mkdtempSync(resolvePath(tmpdir(), "myco-c68-child-"));
    rmSync(childDir, { recursive: true, force: true });
    try {
      const client = await spawn(parentDir);
      try {
        await client.registerAxis({
          name: "curiosity",
          axisClass: "appetite",
          fruitingThreshold: 10.0,
          initialValue: 3.0,
          decayRatePerCycle: 1.0,
          isMortalitySignal: false,
          updateRuleKind: "noop",
        });
        // Send a bare sprout_child request (no envelope) via the low-level path.
        const { MSG_TYPE } = await import("../src/protocol/messages.ts");
        const bare = new Map<
          string,
          import("../src/canonical/canonical_bytes.ts").Value
        >([["child_state_dir", { type: "string", value: childDir }]]);
        await assert.rejects(
          // deno-lint-ignore no-explicit-any
          () => (client as any)._sendRequest(MSG_TYPE.SPROUT_CHILD, bare),
          /C68|unattested|spawn_cosign/,
          "sprout without a spawn-cosign envelope must be refused with C68",
        );
        // No child dag.cb created.
        assert.ok(
          !existsSync(`${childDir}/dag.cb`),
          "C68: refused sprout must NOT create child dag.cb",
        );
      } finally {
        await client.shutdown();
      }
    } finally {
      cleanupDir(parentDir);
      cleanupDir(childDir);
    }
  });

  it("M20: sproutChild refuses to overwrite existing dag.cb", async () => {
    const parentDir = freshStateDir();
    const childDir = freshStateDir(); // already contains a dag.cb after spawn
    // Pre-populate childDir with a dag.cb by spawning a substrate there first.
    const preSpawn = await spawn(childDir);
    await preSpawn.shutdown();
    try {
      const client = await spawn(parentDir);
      try {
        const sporeSchemaCanonicalBytes = await buildTestSporeSchemaBytes();
        // Even WITH a valid envelope, the existing-dag.cb guard fires.
        await assert.rejects(
          () =>
            client.sproutChild({
              childStateDir: childDir,
              sporeSchemaCanonicalBytes,
            }),
          /refusing to overwrite|exists/,
        );
      } finally {
        await client.shutdown();
      }
    } finally {
      cleanupDir(parentDir);
      cleanupDir(childDir);
    }
  });

  it("M20: child substrate boots independently with inherited axes", async () => {
    const parentDir = freshStateDir();
    const childDir = mkdtempSync(resolvePath(tmpdir(), "myco-m20-child-"));
    rmSync(childDir, { recursive: true, force: true });
    try {
      // Parent: register two axes, perturb one.
      const parent = await spawn(parentDir);
      await parent.registerAxis({
        name: "hunger",
        axisClass: "appetite",
        fruitingThreshold: 5.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      await parent.registerAxis({
        name: "vitality",
        axisClass: "decay",
        fruitingThreshold: 0.1,
        initialValue: 1.0,
        decayRatePerCycle: 0.5,
        isMortalitySignal: true,
        updateRuleKind: "decay",
      });
      await parent.perturb("hunger", 2.5);
      const sporeSchemaCanonicalBytes = await buildTestSporeSchemaBytes();
      await parent.sproutChild({
        childStateDir: childDir,
        sporeSchemaCanonicalBytes,
      });
      await parent.shutdown();

      // Spawn child substrate at childDir — it should boot with inherited axes.
      // v0.9 keyless: the child boots with its own random session_secret (no
      // pinned identity to match).
      const child = await spawn(childDir);
      try {
        const snap = await child.snapshot();
        // Both axes inherited with their values.
        assert.equal(snap.size, 2);
        assert.equal(snap.get("hunger"), 2.5, "hunger value inherited");
        assert.equal(snap.get("vitality"), 1.0, "vitality value inherited");

        // Child has its OWN causal history — no parent spore_emission transferred.
        const recent = await child.queryRecentNodes(10n);
        const sporeNodes = recent.nodes.filter((n) =>
          n.nodeType.startsWith("spore_emission:"),
        );
        assert.equal(
          sporeNodes.length,
          0,
          "child should not inherit parent's spore_emission DAG nodes",
        );
      } finally {
        await child.shutdown();
      }
    } finally {
      cleanupDir(parentDir);
      cleanupDir(childDir);
    }
  });

  // -------------------------------------------------------------------------
  // M19 P7 必朽 mortality-proposal tests.
  // -------------------------------------------------------------------------
  it("M19 P7: mortality_signal fruiting auto-emits self_euthanasia_proposal", async () => {
    const client = await spawn();
    try {
      // Register a DECAY axis as mortality signal.
      await client.registerAxis({
        name: "vitality",
        axisClass: "decay",
        fruitingThreshold: 0.1,
        initialValue: 1.0,
        decayRatePerCycle: 0.5,
        isMortalitySignal: true,
        updateRuleKind: "decay",
      });
      // Advance until the mortality signal fires.
      let firedCycle: bigint | null = null;
      let euthanasiaHashes: Uint8Array[] = [];
      for (let c = 1n; c <= 10n; c++) {
        const adv = await client.advance(c);
        if (adv.fruitedAxes.length > 0) {
          firedCycle = c;
          euthanasiaHashes = adv.selfEuthanasiaProposalHashes;
          break;
        }
      }
      assert.ok(firedCycle !== null, "mortality_signal should fire within 10 cycles");
      assert.equal(
        euthanasiaHashes.length,
        1,
        "exactly one self_euthanasia_proposal should be emitted per mortality fruiting",
      );

      // Query DAG: verify the proposal node exists with correct node_type.
      const report = await client.queryRecentNodes(20n, "self_euthanasia_proposal:");
      assert.equal(report.filteredTotal, 1n);
      assert.equal(report.nodes[0]!.nodeType, "self_euthanasia_proposal:vitality");
      // Hash matches what advance reported.
      assert.deepEqual(report.nodes[0]!.hash, euthanasiaHashes[0]);
    } finally {
      await client.shutdown();
    }
  });

  it("M19 P7: non-mortality_signal fruiting does NOT emit self_euthanasia_proposal", async () => {
    const client = await spawn();
    try {
      // Regular appetite axis — not a mortality signal.
      await client.registerAxis({
        name: "hunger",
        axisClass: "appetite",
        fruitingThreshold: 1.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      await client.perturb("hunger", 2.0);
      const adv = await client.advance(1n);
      assert.equal(adv.fruitedAxes.length, 1);
      // Appetite fruiting should NOT spawn a self_euthanasia_proposal.
      assert.equal(adv.selfEuthanasiaProposalHashes.length, 0);

      const report = await client.queryRecentNodes(20n, "self_euthanasia_proposal:");
      assert.equal(report.filteredTotal, 0n);
    } finally {
      await client.shutdown();
    }
  });

  it("M19 P9: run_immune_check exercises C18 canonical_bytes_render_drift on real DAG", async () => {
    const client = await spawn();
    try {
      // Populate the DAG with several legitimate node types.
      await client.registerAxis({
        name: "ax",
        axisClass: "appetite",
        fruitingThreshold: 1.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      await client.perturb("ax", 2.0);
      await client.advance(1n);
      await client.ingestRawMaterial({
        contentKind: "text",
        contentBytes: new TextEncoder().encode("c18 corpus"),
      });
      const report = await client.runImmuneCheck();
      const c18 = report.checks.find((c) => c.checkId === "dag_verify_all");
      assert.ok(c18, "dag_verify_all (C18/C7 family) check should be present");
      assert.equal(c18!.passed, true, c18!.evidence);
    } finally {
      await client.shutdown();
    }
  });

  it("M19: self_euthanasia_proposal persists across substrate restart", async () => {
    const dir = freshStateDir();
    try {
      const c1 = await spawn(dir);
      await c1.registerAxis({
        name: "vitality",
        axisClass: "decay",
        fruitingThreshold: 0.1,
        initialValue: 1.0,
        decayRatePerCycle: 0.5,
        isMortalitySignal: true,
        updateRuleKind: "decay",
      });
      for (let c = 1n; c <= 10n; c++) {
        const adv = await c1.advance(c);
        if (adv.selfEuthanasiaProposalHashes.length > 0) break;
      }
      const pre = await c1.queryRecentNodes(20n, "self_euthanasia_proposal:");
      assert.equal(pre.filteredTotal, 1n);
      await c1.shutdown();

      const c2 = await spawn(dir);
      try {
        const post = await c2.queryRecentNodes(20n, "self_euthanasia_proposal:");
        assert.equal(
          post.filteredTotal,
          1n,
          "self_euthanasia_proposal should survive restart",
        );
      } finally {
        await c2.shutdown();
      }
    } finally {
      cleanupDir(dir);
    }
  });

  // -------------------------------------------------------------------------
  // M21.1 DAG-event emission tests (the operator_pinned / nonce_issued /
  // nonce_consumed emissions were removed with the anchor surface).
  // -------------------------------------------------------------------------
  it("M21.1: fresh substrate emits genesis_event as first DAG node", async () => {
    const client = await spawn();
    try {
      const all = await client.queryRecentNodes(50n);
      const genesis = all.nodes.find((n) =>
        n.nodeType.startsWith("genesis_event:"),
      );
      assert.ok(genesis, "expected genesis_event:* DAG node");
      assert.equal(
        genesis!.parentHashes.length,
        0,
        "genesis_event has no parents",
      );
    } finally {
      await client.shutdown();
    }
  });

  it("M21.1: register_axis emits axis_registered event", async () => {
    const client = await spawn();
    try {
      await client.registerAxis({
        name: "test_emit",
        axisClass: "appetite",
        fruitingThreshold: 5.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      const events = await client.queryRecentNodes(20n, "axis_registered:");
      assert.equal(events.filteredTotal, 1n);
      assert.equal(events.nodes[0]!.nodeType, "axis_registered:test_emit");
    } finally {
      await client.shutdown();
    }
  });

  it("M21.1: perturb_axis emits axis_perturbed event", async () => {
    const client = await spawn();
    try {
      await client.registerAxis({
        name: "p_emit",
        axisClass: "appetite",
        fruitingThreshold: 100.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      await client.perturb("p_emit", 3.5);
      await client.perturb("p_emit", 1.5);
      const events = await client.queryRecentNodes(20n, "axis_perturbed:");
      assert.equal(events.filteredTotal, 2n);
      for (const n of events.nodes) {
        assert.equal(n.nodeType, "axis_perturbed:p_emit");
      }
    } finally {
      await client.shutdown();
    }
  });

  it("M21.1: advance emits cycle_advanced event", async () => {
    const client = await spawn();
    try {
      await client.advance(1n);
      await client.advance(2n);
      const events = await client.queryRecentNodes(20n, "cycle_advanced");
      assert.ok(
        events.filteredTotal >= 2n,
        `expected ≥2 cycle_advanced events; got ${events.filteredTotal}`,
      );
    } finally {
      await client.shutdown();
    }
  });

  it("M21.1: C19 detector passes on healthy substrate", async () => {
    const client = await spawn();
    try {
      // Drive the substrate through several operations to populate state.
      await client.registerAxis({
        name: "c19_test",
        axisClass: "appetite",
        fruitingThreshold: 5.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      await client.perturb("c19_test", 2.5);
      await client.advance(1n);
      // Run integrity check.
      const report = await client.runImmuneCheck();
      const orphanCheck = report.checks.find(
        (c) => c.checkId === "substrate_state_orphan_detected",
      );
      assert.ok(orphanCheck, "expected C19 check to be present");
      assert.equal(
        orphanCheck!.passed,
        true,
        `C19 should pass on healthy substrate; evidence: ${orphanCheck!.evidence}`,
      );
    } finally {
      await client.shutdown();
    }
  });

  it("M21.1: DerivedState reconstructs state correctly across operations", async () => {
    const client = await spawn();
    try {
      // Build up state, then check C19 passes throughout.
      await client.registerAxis({
        name: "derived_test",
        axisClass: "appetite",
        fruitingThreshold: 100.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      const check1 = await client.runImmuneCheck();
      assert.equal(check1.failedChecks, 0n);

      await client.perturb("derived_test", 5.0);
      await client.advance(1n);
      const check2 = await client.runImmuneCheck();
      assert.equal(check2.failedChecks, 0n);

      await client.advance(2n);
      const check3 = await client.runImmuneCheck();
      assert.equal(
        check3.failedChecks,
        0n,
        "C19 should remain green throughout operations",
      );
    } finally {
      await client.shutdown();
    }
  });

  // -------------------------------------------------------------------------
  // M21.5 snapshot.cb + M21.4/M21.3/M21.2 DAG-first boot tests.
  // -------------------------------------------------------------------------
  it("M21.5: snapshot.cb created after K=10 cycles + survives restart", async () => {
    const stateDir = freshStateDir();
    try {
      const c1 = await spawn(stateDir);
      await c1.registerAxis({
        name: "snap_test",
        axisClass: "appetite",
        fruitingThreshold: 100.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      // Advance 10 cycles to trigger snapshot.
      for (let c = 1n; c <= 10n; c++) {
        await c1.advance(c);
      }
      await c1.shutdown();

      // M21.5: snapshot.cb should exist alongside dag.cb.
      // M25.0: substrate_signing_key.cb (substrate-private Ed25519 seed) is also
      // required: it cannot be derived from DAG content. (This is the
      // SUBSTRATE's own signing key for federation, NOT an owner key.)
      // P09: substrate.lock is the single-integument process lock (0-byte OS
      // advisory lockfile created on boot, auto-released on exit; per L1/SKIN §6
      // state_dir-allowed). It remains on disk after a clean exit.
      const fs = await import("node:fs");
      const path = await import("node:path");
      const files = fs.readdirSync(stateDir).filter((f) => !f.endsWith(".tmp")).sort();
      assert.deepEqual(
        files,
        ["dag.cb", "snapshot.cb", "substrate.lock", "substrate_signing_key.cb"],
        `M21.5 + M25.0: expected dag.cb + snapshot.cb + substrate.lock + substrate_signing_key.cb; got: ${files.join(", ")}`,
      );

      // Boot should succeed (uses snapshot for fast Rust-side init).
      const c2 = await spawn(stateDir);
      try {
        const integrity = await c2.runImmuneCheck();
        assert.equal(integrity.failedChecks, 0n);
        // cycle_counter should be 10 (preserved across boot via snapshot).
        const adv = await c2.advance(11n);
        assert.equal(adv.cycleNumber, 11n);
      } finally {
        await c2.shutdown();
      }

      // After more operations, snapshot.cb should still be a regular file.
      assert.ok(fs.statSync(path.join(stateDir, "snapshot.cb")).isFile());
    } finally {
      cleanupDir(stateDir);
    }
  });

  it("M21.5: corrupted snapshot.cb gracefully falls back to full DAG replay", async () => {
    const stateDir = freshStateDir();
    try {
      const c1 = await spawn(stateDir);
      await c1.registerAxis({
        name: "snap_corrupt",
        axisClass: "appetite",
        fruitingThreshold: 100.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      for (let c = 1n; c <= 10n; c++) {
        await c1.advance(c);
      }
      await c1.shutdown();

      // Corrupt snapshot.cb.
      const fs = await import("node:fs");
      const path = await import("node:path");
      fs.writeFileSync(path.join(stateDir, "snapshot.cb"), Buffer.from("corrupted junk"));

      // Boot should succeed — falls back to full DAG replay.
      const c2 = await spawn(stateDir);
      try {
        const adv = await c2.advance(11n);
        assert.equal(adv.cycleNumber, 11n);
        const integrity = await c2.runImmuneCheck();
        assert.equal(integrity.failedChecks, 0n);
      } finally {
        await c2.shutdown();
      }
    } finally {
      cleanupDir(stateDir);
    }
  });

  it("M21.4 acid test: substrate state_dir contains only DAG-first artifacts after operations", async () => {
    // M21.4: legacy state files (manifest.cb / gradient.cb / owner_keys.cb /
    // operator_identity_pubkey.cb / nonces.cb) are no longer written. dag.cb is
    // the substrate's authoritative artifact; snapshot.cb (cache) +
    // substrate_signing_key.cb (substrate-private secret) are the only other
    // allowed files.
    const stateDir = freshStateDir();
    const client = await spawn(stateDir);
    try {
      // Drive a variety of keyless operations.
      await client.registerAxis({
        name: "m21_4",
        axisClass: "appetite",
        fruitingThreshold: 10.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      await client.perturb("m21_4", 3.0);
      await client.advance(1n);
      await client.submitMutation({
        mutationType: "delta_absorb",
        contentCanonicalBytes: new TextEncoder().encode("m21.4 single-file test"),
      });
    } finally {
      await client.shutdown();
    }

    // After shutdown, the state_dir must contain ONLY:
    // - dag.cb (authoritative substrate state, M21.4)
    // - snapshot.cb (optional cache, M21.5: present if any K=10 cycle happened)
    // - substrate_signing_key.cb (substrate-private Ed25519 seed, M25.0)
    // - substrate.lock (P09 single-integument lock: 0-byte OS advisory lockfile
    //   created on boot, auto-released on exit; L1/SKIN §6 state_dir-allowed)
    const fs = await import("node:fs");
    const files = fs
      .readdirSync(stateDir)
      .filter((f) => !f.endsWith(".tmp"))
      .sort();
    const allowed = new Set(["dag.cb", "snapshot.cb", "substrate.lock", "substrate_signing_key.cb"]);
    for (const f of files) {
      assert.ok(
        allowed.has(f),
        `M21.4 + M25.0: unexpected state file: ${f}. Only dag.cb + (optional) snapshot.cb + substrate_signing_key.cb allowed.`,
      );
    }
    assert.ok(files.includes("dag.cb"), "dag.cb must exist");
    assert.ok(
      files.includes("substrate_signing_key.cb"),
      "M25.0: substrate_signing_key.cb must exist (substrate-private signing seed)",
    );
    cleanupDir(stateDir);
  });

  it("M21.3 acid test: Python gradient state recovers from DAG-only restart", async () => {
    // The deepest M21.3 test: delete EVERY state file except dag.cb. The
    // substrate must boot, replay DAG events, reconstruct Python's gradient
    // state in-memory, and snapshot the same axis values as before.
    const stateDir = freshStateDir();
    try {
      // Session 1: build up gradient state.
      const c1 = await spawn(stateDir);
      await c1.registerAxis({
        name: "m21_3_axis_a",
        axisClass: "appetite",
        fruitingThreshold: 10.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      await c1.registerAxis({
        name: "m21_3_axis_b",
        axisClass: "decay",
        fruitingThreshold: 0.1,
        initialValue: 1.0,
        decayRatePerCycle: 0.9,
        isMortalitySignal: false,
        updateRuleKind: "decay",
      });
      await c1.perturb("m21_3_axis_a", 2.5);
      await c1.perturb("m21_3_axis_a", 1.5);
      const preSnap = await c1.snapshot();
      const preA = preSnap.get("m21_3_axis_a");
      const preB = preSnap.get("m21_3_axis_b");
      await c1.shutdown();

      // Delete EVERYTHING in state dir except dag.cb.
      const fs = await import("node:fs");
      const path = await import("node:path");
      const before = fs.readdirSync(stateDir);
      for (const e of before) {
        if (e !== "dag.cb") {
          fs.rmSync(path.join(stateDir, e), { force: true, recursive: true });
        }
      }
      const after = fs.readdirSync(stateDir);
      assert.deepEqual(after, ["dag.cb"]);

      // Session 2: boot purely from DAG. Python state should be reconstructed
      // via DAG event replay. Snapshot must match pre-shutdown values.
      const c2 = await spawn(stateDir);
      try {
        const postSnap = await c2.snapshot();
        assert.equal(postSnap.size, 2, "both axes should be reconstructed");
        assert.equal(
          postSnap.get("m21_3_axis_a"),
          preA,
          "axis_a value should be replayed (initial + 2 perturbations)",
        );
        assert.equal(
          postSnap.get("m21_3_axis_b"),
          preB,
          "axis_b value should be replayed (initial_value=1.0 since no perturbations)",
        );
        // Integrity should be intact.
        const integrity = await c2.runImmuneCheck();
        assert.equal(integrity.failedChecks, 0n);
      } finally {
        await c2.shutdown();
      }
    } finally {
      cleanupDir(stateDir);
    }
  });

  it("M21.2: substrate boots from DAG even with state files deleted (except dag.cb)", async () => {
    const stateDir = freshStateDir();
    try {
      // Session 1: build up substrate state (keyless).
      const c1 = await spawn(stateDir);
      await c1.registerAxis({
        name: "m21_dag_only",
        axisClass: "appetite",
        fruitingThreshold: 10.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      await c1.perturb("m21_dag_only", 3.5);
      await c1.advance(1n);
      await c1.submitMutation({
        mutationType: "delta_absorb",
        contentCanonicalBytes: new TextEncoder().encode("dag-only boot test"),
      });
      await c1.shutdown();

      // Delete EVERYTHING in state dir EXCEPT dag.cb (also snapshot.cb if
      // present from M21.5; we want to test full DAG replay).
      const fs = await import("node:fs");
      const path = await import("node:path");
      const entries = fs.readdirSync(stateDir);
      for (const e of entries) {
        if (e !== "dag.cb") {
          fs.rmSync(path.join(stateDir, e), { force: true, recursive: true });
        }
      }
      const afterDelete = fs.readdirSync(stateDir);
      assert.deepEqual(afterDelete, ["dag.cb"], "only dag.cb should remain");

      // Session 2: boot from DAG only. Should recover everything Rust-side.
      const c2 = await spawn(stateDir);
      try {
        // Check that the integrity check (including C19) passes — proves
        // derived state matches in-memory state after DAG-only boot.
        const integrityReport = await c2.runImmuneCheck();
        assert.equal(
          integrityReport.failedChecks,
          0n,
          `all integrity checks should pass after DAG-only boot; failures: ${integrityReport.checks
            .filter((c) => !c.passed)
            .map((c) => `${c.checkId}: ${c.evidence}`)
            .join(" | ")}`,
        );
        // The accepted daily mutation node survives the DAG-only boot.
        const mut = await c2.queryRecentNodes(50n, "mutation:");
        assert.ok(
          mut.filteredTotal >= 1n,
          "the accepted mutation should be present after DAG-only boot",
        );
      } finally {
        await c2.shutdown();
      }
    } finally {
      cleanupDir(stateDir);
    }
  });

  it("M21.2: legacy substrate (no genesis_event) auto-migrates on boot", async () => {
    const stateDir = freshStateDir();
    try {
      // Spawn once to get a normal substrate state, then surgically delete
      // dag.cb (simulating a pre-M21.1 substrate that has state files but no
      // DAG events).
      const c1 = await spawn(stateDir);
      await c1.shutdown();
      const fs = await import("node:fs");
      const path = await import("node:path");
      fs.rmSync(path.join(stateDir, "dag.cb"), { force: true });
      const before = fs.readdirSync(stateDir);
      assert.ok(!before.includes("dag.cb"));

      // Now boot again — substrate sees no dag.cb. Should auto-emit genesis_event.
      const c2 = await spawn(stateDir);
      try {
        const events = await c2.queryRecentNodes(20n, "genesis_event:");
        assert.equal(
          events.filteredTotal,
          1n,
          "auto-migration should emit exactly 1 genesis_event",
        );
        // After migration, integrity check should pass.
        const integrity = await c2.runImmuneCheck();
        assert.equal(integrity.failedChecks, 0n);
      } finally {
        await c2.shutdown();
      }
    } finally {
      cleanupDir(stateDir);
    }
  });

  // -------------------------------------------------------------------------
  // M25.5 — operator-facing federation + mortality + observatory methods.
  // -------------------------------------------------------------------------

  it("m25_5_federation_open_close_listener_e2e", async () => {
    const client = await spawn();
    try {
      // Open on port-0 → OS picks port.
      const opened = await client.federationOpenListener({
        bindAddr: "127.0.0.1:0",
      });
      assert.ok(opened.boundAddr.startsWith("127.0.0.1:"));
      assert.notEqual(opened.boundAddr, "127.0.0.1:0", "OS picked real port");
      assert.equal(opened.listenerOpenedEventHash.length, 32);

      // Status reflects the listener.
      const status1 = await client.federationStatus();
      assert.equal(status1.isListening, true);
      assert.equal(status1.boundAddr, opened.boundAddr);
      assert.equal(status1.peerCount, 0n);

      // Close the listener.
      const closed = await client.federationCloseListener();
      assert.equal(closed.wasListening, true);
      assert.equal(closed.priorBindAddr, opened.boundAddr);
      assert.ok(closed.listenerClosedEventHash !== null);
      assert.equal(closed.listenerClosedEventHash!.length, 32);

      // Status reflects the close.
      const status2 = await client.federationStatus();
      assert.equal(status2.isListening, false);
      assert.equal(status2.boundAddr, "");

      // Idempotent: closing again returns wasListening=false.
      const closed2 = await client.federationCloseListener();
      assert.equal(closed2.wasListening, false);
      assert.equal(closed2.listenerClosedEventHash, null);
    } finally {
      await client.shutdown();
    }
  });

  it("m25_5_federation_status_empty_substrate", async () => {
    const client = await spawn();
    try {
      const status = await client.federationStatus();
      assert.equal(status.isListening, false);
      assert.equal(status.boundAddr, "");
      assert.equal(status.peerCount, 0n);
      assert.equal(status.eventsReceivedTotal, 0n);
      assert.equal(status.eventsSentTotal, 0n);
    } finally {
      await client.shutdown();
    }
  });

  it("m25_5_federation_connect_peer_two_substrates_pin_each_other", async () => {
    // Spawn two substrates (keyless — each self-mints a distinct substrate_id).
    const state1 = freshStateDir();
    const state2 = freshStateDir();
    let client1: SubstrateClient | null = null;
    let client2: SubstrateClient | null = null;
    try {
      client1 = await spawn(state1);
      client2 = await spawn(state2);

      // Substrate 1 opens listener; substrate 2 connects.
      const opened = await client1.federationOpenListener({
        bindAddr: "127.0.0.1:0",
      });
      const connect = await client2.federationConnectPeer({
        remoteAddr: opened.boundAddr,
      });
      assert.equal(connect.outcome, "pinned");
      assert.ok(connect.peerSubstrateId);
      assert.equal(connect.peerSubstrateId!.length, 32);
      assert.ok(connect.peerPinnedEventHash);
      assert.equal(connect.peerPinnedEventHash!.length, 32);

      // Substrate 2 should report 1 peer pinned (substrate 1).
      const status2 = await client2.federationStatus();
      assert.equal(status2.peerCount, 1n, "substrate 2 has substrate 1 pinned");

      // Substrate 1 should pin substrate 2 via its autonomous tick OR via
      // explicit federation_poll. We confirm pinning via status.
      let status1: FederationStatusResult | null = null;
      for (let i = 0; i < 60; i++) {
        await client1.federationPoll();
        const s = await client1.federationStatus();
        if (s.peerCount >= 1n) {
          status1 = s;
          break;
        }
        await new Promise<void>((r) => setTimeout(r, 50));
      }
      assert.ok(
        status1 !== null,
        "substrate 1 should pin substrate 2 within 3s of dial completion",
      );
      assert.equal(status1!.peerCount, 1n, "substrate 1 has substrate 2 pinned");
    } finally {
      if (client1) await client1.shutdown();
      if (client2) await client2.shutdown();
      cleanupDir(state1);
      cleanupDir(state2);
    }
  });

  it("m25_5_federation_poll_empty_returns_zero_counts", async () => {
    const client = await spawn();
    try {
      // Open a listener but no peers connect.
      await client.federationOpenListener({ bindAddr: "127.0.0.1:0" });
      const poll = await client.federationPoll();
      assert.equal(poll.acceptedConnections, 0n);
      assert.equal(poll.pinnedPeers, 0n);
      assert.equal(poll.rejectedPeers, 0n);
      assert.equal(poll.eventBatchesSent, 0n);
    } finally {
      await client.shutdown();
    }
  });

  it("m25_5_federation_pull_events_unknown_peer_rejected", async () => {
    const client = await spawn();
    try {
      // Pull from a peer that was never pinned. Substrate rejects this
      // with a Protocol error — the call should throw.
      const unknownPeerId = new Uint8Array(32).fill(0xaa);
      await assert.rejects(
        () =>
          client.federationPullEventsFromPeer({
            peerSubstrateId: unknownPeerId,
          }),
        /not pinned|unknown peer|peer/i,
      );
    } finally {
      await client.shutdown();
    }
  });

  it("m25_5_federation_link_to_parent_from_hint_no_hint_returns_false", async () => {
    // Fresh substrate has no parent_federation_hint event. Substrate should
    // report hint_found=false without error.
    const client = await spawn();
    try {
      const result = await client.federationLinkToParentFromHint();
      assert.equal(result.hintFound, false);
      assert.equal(result.alreadyLinked, false);
      assert.equal(result.parentSubstrateId, null);
      assert.equal(result.parentFederationAddr, null);
      assert.equal(result.parentLinkedEventHash, null);
    } finally {
      await client.shutdown();
    }
  });

  it("m25_5_lift_birth_period_quarantine_returns_was_in_quarantine_false_when_not_in_quarantine", async () => {
    // Fresh top-level substrate is never in quarantine. Lift (KEYLESS v0.9 —
    // no owner signature) should succeed with wasInQuarantine=false + no event.
    const client = await spawn();
    try {
      const result = await client.liftBirthPeriodQuarantine();
      assert.equal(result.wasInQuarantine, false);
      assert.equal(result.quarantineLiftedEventHash, null);
    } finally {
      await client.shutdown();
    }
  });

  it("m25_5_accept_self_euthanasia_proposal_terminates_client", async () => {
    // Drive substrate to mortality_signal fruiting, then accept the proposal
    // (KEYLESS v0.9 — a deliberate accept referencing the real proposal).
    // Substrate must gracefully shut down after responding.
    const client = await spawn();
    try {
      await client.registerAxis({
        name: "vitality",
        axisClass: "decay",
        fruitingThreshold: 0.1,
        initialValue: 1.0,
        decayRatePerCycle: 0.5,
        isMortalitySignal: true,
        updateRuleKind: "decay",
      });
      // Advance until the mortality signal fires.
      let proposalHash: Uint8Array | null = null;
      for (let c = 1n; c <= 10n; c++) {
        const adv = await client.advance(c);
        if (adv.selfEuthanasiaProposalHashes.length > 0) {
          proposalHash = adv.selfEuthanasiaProposalHashes[0]!;
          break;
        }
      }
      assert.ok(proposalHash, "mortality_signal should fire within 10 cycles");

      const result = await client.acceptSelfEuthanasiaProposal({
        proposalHash: proposalHash!,
      });
      assert.equal(result.axisName, "vitality");
      assert.equal(result.executedEventHash.length, 32);

      // Substrate gracefully shuts down. Verify the child exits.
      const child = (client as unknown as { child: { once: (e: string, f: () => void) => void; exitCode: number | null } }).child;
      if (child.exitCode === null) {
        await new Promise<void>((resolve, reject) => {
          const t = setTimeout(
            () => reject(new Error("substrate did not exit within 5s")),
            5000,
          );
          child.once("exit", () => {
            clearTimeout(t);
            resolve();
          });
        });
      }
    } finally {
      // shutdown() is harmless if already exited.
      try {
        await client.shutdown();
      } catch {
        // Expected — substrate already exited cleanly.
      }
    }
  });

  it("m25_5_accept_self_euthanasia_proposal_rejects_unknown_proposal", async () => {
    // KEYLESS v0.9: a proposal_hash pointing to no real self_euthanasia_proposal
    // node must be rejected, and the substrate must stay alive (death cannot be
    // triggered on an arbitrary hash).
    const client = await spawn();
    try {
      // An all-zero hash references no proposal node.
      const bogus = new Uint8Array(32);
      await assert.rejects(
        () => client.acceptSelfEuthanasiaProposal({ proposalHash: bogus }),
        /not found in DAG|not a self_euthanasia_proposal/i,
      );
      // Substrate must be alive — confirm by issuing another query.
      const status = await client.federationStatus();
      assert.equal(status.isListening, false);
    } finally {
      await client.shutdown();
    }
  });

  it("m25_5_query_substrate_observatory_format_v2_or_greater", async () => {
    // Fresh substrate, observatory query without window — signal_1 always
    // present, signal_2/3/4/10 present at format_version >= 2.
    const client = await spawn();
    try {
      // Make the DAG non-trivial so signals carry meaningful values.
      await client.registerAxis({
        name: "obs_axis",
        axisClass: "appetite",
        fruitingThreshold: 100.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      await client.perturb("obs_axis", 1.0);
      await client.advance(1n);

      const snap = await client.querySubstrateObservatory();
      assert.ok(
        snap.formatVersion >= 2n,
        `expected format_version >= 2; got ${snap.formatVersion}`,
      );
      assert.ok(snap.capturedAtUnixNs > 0n);

      // Signal #1 is always emitted (Phase α).
      assert.ok(snap.signal1, "signal_1 must be present in any observatory response");
      assert.ok(snap.signal1!.dagNodeCount > 0n);
      assert.ok(snap.signal1!.dagEdgeCount >= 0n);
      assert.ok(snap.signal1!.dagTotalContentBytes > 0n);
      assert.equal(snap.signal1!.manifestCycleCounter, 1n);

      // No window supplied → signal_6 absent.
      assert.equal(snap.signal6, undefined, "signal_6 should be absent when no window supplied");

      // format_version >= 2 → signals 2/3/4 must be present.
      assert.ok(snap.signal2, "signal_2 must be present at format_version >= 2");
      assert.ok(snap.signal3, "signal_3 must be present at format_version >= 2");
      assert.ok(snap.signal4, "signal_4 must be present at format_version >= 2");
      assert.equal(snap.signal4!.signal4bReachablePeerCount, 0n);
      assert.equal(snap.signal3!.distinctPerturbedAxesCount, 1n);

      // M26.2: composite is signal_10 (was signal_7 at v3).
      assert.ok(snap.signal10, "signal_10 (composite) must be present at format_version >= 4");
      assert.ok(Number.isFinite(snap.signal10!.compositeHealthScore));

      // M26.2: cost signals 7/8/9 land at v4.
      if (snap.formatVersion >= 4n) {
        assert.ok(snap.signal7, "signal_7 (compute/cycle) must be present at v4");
        assert.ok(
          snap.signal7!.currentCycleNs > 0n,
          "signal_7 currentCycleNs must reflect real wall-clock work in the cycle",
        );
        assert.ok(snap.signal8, "signal_8 (network/cycle) must be present at v4");
        assert.equal(snap.signal8!.currentCycleBytes, 0n);
        assert.ok(snap.signal9, "signal_9 (storage/cycle) must be present at v4");
        assert.ok(
          snap.signal9!.currentCycleBytes > 0n,
          "signal_9 currentCycleBytes must reflect on-disk growth this cycle",
        );
      }

      // v5 (OBSERVATORY gap) — saturation_status + CHAR07 surfaces parse.
      if (snap.formatVersion >= 5n) {
        assert.ok(
          snap.saturationStatus,
          "saturation_status must be present at v5",
        );
        assert.equal(
          snap.saturationStatus!.raw.get("stage")?.type,
          "string",
          "saturation_status.stage must be a string",
        );
        assert.ok(snap.char07, "char07 surface must be present at v5");
        // CHAR05 honesty: capability_asymmetry is NOT autonomously observable,
        // so with no cultivator attestation its source is "unavailable".
        const capSource = snap.char07!.capabilityAsymmetry.get("source");
        assert.equal(
          capSource?.type === "string" ? capSource.value : undefined,
          "unavailable",
          "capability_asymmetry must be 'unavailable' until cultivator attests",
        );
        assert.equal(
          snap.char07!.honestDisagreement.get("density")?.type,
          "uint",
          "char07 honest_disagreement.density must be a uint",
        );
      }
    } finally {
      await client.shutdown();
    }
  });

  it("m25_5_query_substrate_observatory_signal_6_populated_when_window_supplied", async () => {
    const client = await spawn();
    try {
      const snap = await client.querySubstrateObservatory({
        operatorAttestedContextWindowBytes: 200_000n,
      });
      assert.ok(snap.signal6, "signal_6 must be present when window supplied");
      assert.equal(snap.signal6!.operatorAttestedContextWindowBytes, 200_000n);
      assert.ok(
        snap.signal6!.substrateTotalBytes >= 0n,
        "substrate_total_bytes must be a real count",
      );
      // ratio must equal substrate_total / window (as Number).
      const expectedRatio =
        Number(snap.signal6!.substrateTotalBytes) /
        Number(snap.signal6!.operatorAttestedContextWindowBytes);
      assert.ok(
        Math.abs(snap.signal6!.ratio - expectedRatio) < 1e-9,
        `ratio mismatch: got ${snap.signal6!.ratio}, expected ~${expectedRatio}`,
      );
    } finally {
      await client.shutdown();
    }
  });

  // -------------------------------------------------------------------------
  // **M26.3 P10 Selective Compression** + **M26.4 F20 owner-objective**
  // (KEYLESS v0.9 — the substrate classifies compression / owner_objective by
  // mutation_type + content; the owner Ed25519 attestation gate was removed, so
  // these submit WITHOUT a signature/nonce. The P10.b invariant-set + the
  // empty-weights checks remain content-driven and still fire).
  // -------------------------------------------------------------------------

  it("M26.3: compression mutation accepted + emits compression_event:{rule_id}", async () => {
    const client = await spawn();
    try {
      const { encode: cbEncode } = await import(
        "../src/canonical/canonical_bytes.ts"
      );
      const tipBytes = new Uint8Array(32); // all-zero tip (substrate accepts)
      const witnessMap: Map<string, import("../src/canonical/canonical_bytes.ts").Value> =
        new Map();
      witnessMap.set("rule_id", {
        type: "string",
        value: "raw_material_aggregate_v1",
      });
      witnessMap.set("compressed_node_hashes", { type: "array", value: [] });
      witnessMap.set("aggregate_summary", {
        type: "bytes",
        value: new TextEncoder().encode("M26.3 e2e test aggregate"),
      });
      witnessMap.set("attestation_dag_tip", { type: "bytes", value: tipBytes });
      witnessMap.set("semantic_lossy", { type: "bool", value: true });
      witnessMap.set("causal_recoverability_argument", {
        type: "string",
        value: "no-op compression: empty hash list, vacuously preserves invariants",
      });
      const witnessBytes = cbEncode({ type: "map", value: witnessMap }).bytes;

      const result = await client.submitMutation({
        mutationType: "compression",
        contentCanonicalBytes: witnessBytes,
      });
      assert.equal(
        result.accepted,
        true,
        `valid compression mutation must accept; got rejection: ${result.rejectionReason}`,
      );
      assert.equal(result.classification, "contract_identity_level");

      // Verify compression_event:raw_material_aggregate_v1 landed in the DAG.
      const nodes = await client.queryRecentNodes(50n, "compression_event:");
      assert.ok(
        nodes.nodes.length >= 1,
        "compression_event:* must appear in DAG after accepted compression mutation",
      );
      const found = nodes.nodes.find((n) =>
        n.nodeType.endsWith(":raw_material_aggregate_v1"),
      );
      assert.ok(
        found,
        `compression_event:raw_material_aggregate_v1 not found; saw ${nodes.nodes.map((n) => n.nodeType).join(", ")}`,
      );
    } finally {
      await client.shutdown();
    }
  });

  it("M26.4: owner_objective_declaration accepted + emits owner_objective_declared:{id}", async () => {
    const client = await spawn();
    try {
      const { encode: cbEncode } = await import(
        "../src/canonical/canonical_bytes.ts"
      );
      const objectiveMap: Map<string, import("../src/canonical/canonical_bytes.ts").Value> =
        new Map();
      objectiveMap.set("objective_id", {
        type: "string",
        value: "m26_4_ts_e2e_objective",
      });
      objectiveMap.set("declared_at_cycle", { type: "uint", value: 0n });
      const weightEntry1: Map<string, import("../src/canonical/canonical_bytes.ts").Value> =
        new Map();
      weightEntry1.set("prefix", { type: "string", value: "axis_perturbed:" });
      weightEntry1.set("weight_repr", { type: "string", value: "0.75" });
      const weightEntry2: Map<string, import("../src/canonical/canonical_bytes.ts").Value> =
        new Map();
      weightEntry2.set("prefix", { type: "string", value: "raw_material:" });
      weightEntry2.set("weight_repr", { type: "string", value: "0.25" });
      objectiveMap.set("weights", {
        type: "array",
        value: [
          { type: "map", value: weightEntry1 },
          { type: "map", value: weightEntry2 },
        ],
      });
      const objectiveBytes = cbEncode({ type: "map", value: objectiveMap }).bytes;

      const result = await client.submitMutation({
        mutationType: "owner_objective_declaration",
        contentCanonicalBytes: objectiveBytes,
      });
      assert.equal(
        result.accepted,
        true,
        `valid owner_objective_declaration must accept; got rejection: ${result.rejectionReason}`,
      );
      assert.equal(result.classification, "contract_identity_level");

      // Verify owner_objective_declared:m26_4_ts_e2e_objective lands.
      const nodes = await client.queryRecentNodes(50n, "owner_objective_declared:");
      assert.ok(
        nodes.nodes.length >= 1,
        "owner_objective_declared:* must appear after the mutation",
      );
      const found = nodes.nodes.find((n) =>
        n.nodeType.endsWith(":m26_4_ts_e2e_objective"),
      );
      assert.ok(
        found,
        `expected owner_objective_declared:m26_4_ts_e2e_objective; saw: ${nodes.nodes.map((n) => n.nodeType).join(", ")}`,
      );
    } finally {
      await client.shutdown();
    }
  });

  it("M26.4: owner_objective_declaration with empty weights is rejected via C5", async () => {
    const client = await spawn();
    try {
      const { encode: cbEncode } = await import(
        "../src/canonical/canonical_bytes.ts"
      );
      const objectiveMap: Map<string, import("../src/canonical/canonical_bytes.ts").Value> =
        new Map();
      objectiveMap.set("objective_id", {
        type: "string",
        value: "empty_weights_rejected",
      });
      objectiveMap.set("declared_at_cycle", { type: "uint", value: 0n });
      objectiveMap.set("weights", { type: "array", value: [] });
      const objectiveBytes = cbEncode({ type: "map", value: objectiveMap }).bytes;
      const result = await client.submitMutation({
        mutationType: "owner_objective_declaration",
        contentCanonicalBytes: objectiveBytes,
      });
      assert.equal(
        result.accepted,
        false,
        "empty-weights owner_objective_declaration must be rejected",
      );
      assert.match(
        result.rejectionReason,
        /weights array MUST be non-empty/i,
        `rejection reason should mention empty weights; got: ${result.rejectionReason}`,
      );
    } finally {
      await client.shutdown();
    }
  });

  it("M26.3: compression targeting an invariant-set member is rejected with C51", async () => {
    const client = await spawn();
    try {
      // Find the genesis_event node hash (an invariant-set member).
      const recent = await client.queryRecentNodes(20n, "genesis_event:");
      assert.ok(
        recent.nodes.length >= 1,
        "genesis_event:* must be present in fresh substrate DAG",
      );
      const genesisHash = recent.nodes[0]!.hash;
      assert.equal(genesisHash.length, 32, "genesis hash is 32 bytes");

      // Build a compression witness targeting the genesis_event hash —
      // this MUST be rejected by P10.b invariant set protection (C51).
      const { encode: cbEncode } = await import(
        "../src/canonical/canonical_bytes.ts"
      );
      const tipBytes = new Uint8Array(32);
      const witnessMap: Map<string, import("../src/canonical/canonical_bytes.ts").Value> =
        new Map();
      witnessMap.set("rule_id", {
        type: "string",
        value: "raw_material_aggregate_v1",
      });
      witnessMap.set("compressed_node_hashes", {
        type: "array",
        value: [{ type: "bytes", value: genesisHash }],
      });
      witnessMap.set("aggregate_summary", {
        type: "bytes",
        value: new Uint8Array([0]),
      });
      witnessMap.set("attestation_dag_tip", { type: "bytes", value: tipBytes });
      witnessMap.set("semantic_lossy", { type: "bool", value: true });
      witnessMap.set("causal_recoverability_argument", {
        type: "string",
        value: "intentionally violating P10.b for test",
      });
      const witnessBytes = cbEncode({ type: "map", value: witnessMap }).bytes;
      const result = await client.submitMutation({
        mutationType: "compression",
        contentCanonicalBytes: witnessBytes,
      });
      assert.equal(
        result.accepted,
        false,
        "compression targeting genesis_event (P10.b invariant) must be rejected",
      );
      assert.match(
        result.rejectionReason,
        /P10\.b|compression_invariant_corruption/i,
        `rejection reason should mention P10.b; got: ${result.rejectionReason}`,
      );
      // Verify C51 immune event landed.
      const immune = await client.queryImmuneEvents();
      const c51 = immune.events.find((e) =>
        e.nodeType.includes("C51_compression_invariant_corruption"),
      );
      assert.ok(
        c51,
        `C51_compression_invariant_corruption must fire on P10.b breach; saw: ${immune.events.map((e) => e.nodeType).join(", ")}`,
      );
    } finally {
      await client.shutdown();
    }
  });
});
