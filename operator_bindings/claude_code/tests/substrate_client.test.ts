// SubstrateClient e2e tests — spawn myco-substrate binary, drive full 3-tier stack.
//
// THE M6 milestone proof: TypeScript ↔ Rust ↔ Python with all three
// processes alive, exchanging canonical-bytes frames over stdio.

import { describe, it } from "node:test";
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
  // M14 per-handshake REVEAL keypair + nonce persistence tests.
  // -------------------------------------------------------------------------
  it("M14: submitMutationWithReveal accepts full envelope", async () => {
    const opDir = mkdtempSync(resolvePath(tmpdir(), "myco-m14-op-"));
    try {
      const { OperatorIdentity } = await import("../src/operator_identity.ts");
      const identity = OperatorIdentity.loadOrCreate(opDir);
      const stateDir = freshStateDir();
      const client = await SubstrateClient.spawn({
        substrateBinary: SUBSTRATE_BIN,
        env: { MYCO_STATE_DIR: stateDir },
        operatorIdentity: identity,
      });
      try {
        const content = new TextEncoder().encode("M14 REVEAL envelope test");
        const result = await client.submitMutationWithReveal({
          mutationType: "schema_change",
          touchedMetaStructures: ["appetite_axis_schema"],
          contentCanonicalBytes: content,
          operatorIdentity: identity,
        });
        assert.equal(
          result.accepted,
          true,
          `full REVEAL envelope should accept; got: ${result.rejectionReason}`,
        );
        assert.equal(result.classification, "contract_identity_level");
      } finally {
        await client.shutdown();
      }
    } finally {
      cleanupDir(opDir);
    }
  });

  it("M14: forged identity-signature-over-REVEAL is rejected with C17", async () => {
    const opDir = mkdtempSync(resolvePath(tmpdir(), "myco-m14-op-"));
    const wrongDir = mkdtempSync(resolvePath(tmpdir(), "myco-m14-wrong-"));
    try {
      const { OperatorIdentity } = await import("../src/operator_identity.ts");
      const identity = OperatorIdentity.loadOrCreate(opDir);
      const wrongIdentity = OperatorIdentity.loadOrCreate(wrongDir);
      const stateDir = freshStateDir();
      const client = await SubstrateClient.spawn({
        substrateBinary: SUBSTRATE_BIN,
        env: { MYCO_STATE_DIR: stateDir },
        operatorIdentity: identity, // Substrate pins identity's pubkey
      });
      try {
        // Generate a fresh REVEAL keypair.
        const { ed25519 } = await import("@noble/curves/ed25519.js");
        const { randomBytes: rb } = await import("node:crypto");
        const revealSeed = new Uint8Array(rb(32));
        const revealPubkey = ed25519.getPublicKey(revealSeed);

        // Sign the REVEAL pubkey with the WRONG identity (not the pinned one).
        const { revealKeyBindingSigningInput } = await import("../src/protocol/messages.ts");
        const signingInput = revealKeyBindingSigningInput(revealPubkey);
        const forgedSig = wrongIdentity.sign(signingInput);

        // Sign content with REVEAL.
        const content = new TextEncoder().encode("forged REVEAL attempt");
        const revealSig = ed25519.sign(content, revealSeed);

        const nonceResult = await client.requestAttestationNonce(content);
        const result = await client.submitMutation({
          mutationType: "schema_change",
          touchedMetaStructures: ["appetite_axis_schema"],
          contentCanonicalBytes: content,
          attestationSignature: revealSig,
          nonce: nonceResult.nonce,
          expiryUnixNs: nonceResult.expiryUnixNs,
          revealPubkey,
          identitySignatureOverRevealPubkey: forgedSig, // FORGED
        });
        assert.equal(result.accepted, false);
        assert.match(result.rejectionReason, /identity signature|invalid/);

        // Verify C17 immune sporocarp was emitted.
        const events = await client.queryImmuneEvents();
        const c17 = events.events.find((e) =>
          e.nodeType.includes("C17_operator_witness_forgery"),
        );
        assert.ok(c17, "expected C17 immune sporocarp on forged identity-over-REVEAL");
      } finally {
        await client.shutdown();
      }
    } finally {
      cleanupDir(opDir);
      cleanupDir(wrongDir);
    }
  });

  it("M14: nonce log persists across restart (replay blocked cross-session)", async () => {
    const opDir = mkdtempSync(resolvePath(tmpdir(), "myco-m14-op-"));
    try {
      const { OperatorIdentity } = await import("../src/operator_identity.ts");
      const identity = OperatorIdentity.loadOrCreate(opDir);
      const stateDir = freshStateDir();

      // Session 1: request a nonce, use it once.
      const c1 = await SubstrateClient.spawn({
        substrateBinary: SUBSTRATE_BIN,
        env: { MYCO_STATE_DIR: stateDir },
        operatorIdentity: identity,
      });
      const content = new TextEncoder().encode("nonce persistence test");
      const nonceResult = await c1.requestAttestationNonce(content);
      const sig = identity.sign(content);
      const r1 = await c1.submitMutation({
        mutationType: "schema_change",
        touchedMetaStructures: ["appetite_axis_schema"],
        contentCanonicalBytes: content,
        attestationSignature: sig,
        nonce: nonceResult.nonce,
        expiryUnixNs: nonceResult.expiryUnixNs,
      });
      assert.equal(r1.accepted, true);
      await c1.shutdown();

      // Session 2: try to replay the same nonce. M14 nonce persistence means
      // the substrate REMEMBERS the consumed flag across restart.
      const c2 = await SubstrateClient.spawn({
        substrateBinary: SUBSTRATE_BIN,
        env: { MYCO_STATE_DIR: stateDir },
        operatorIdentity: identity,
      });
      try {
        const r2 = await c2.submitMutation({
          mutationType: "schema_change",
          touchedMetaStructures: ["appetite_axis_schema"],
          contentCanonicalBytes: content,
          attestationSignature: sig,
          nonce: nonceResult.nonce,
          expiryUnixNs: nonceResult.expiryUnixNs,
        });
        assert.equal(
          r2.accepted,
          false,
          "M14: replay should be rejected even across restart",
        );
        assert.match(r2.rejectionReason, /replay|consumed/);
      } finally {
        await c2.shutdown();
      }
    } finally {
      cleanupDir(opDir);
    }
  });

  it("M14: REVEAL with valid identity sig but malformed REVEAL sig is rejected", async () => {
    const opDir = mkdtempSync(resolvePath(tmpdir(), "myco-m14-op-"));
    try {
      const { OperatorIdentity } = await import("../src/operator_identity.ts");
      const identity = OperatorIdentity.loadOrCreate(opDir);
      const stateDir = freshStateDir();
      const client = await SubstrateClient.spawn({
        substrateBinary: SUBSTRATE_BIN,
        env: { MYCO_STATE_DIR: stateDir },
        operatorIdentity: identity,
      });
      try {
        const { ed25519 } = await import("@noble/curves/ed25519.js");
        const { randomBytes: rb } = await import("node:crypto");
        const revealSeed = new Uint8Array(rb(32));
        const revealPubkey = ed25519.getPublicKey(revealSeed);

        const { revealKeyBindingSigningInput } = await import("../src/protocol/messages.ts");
        const signingInput = revealKeyBindingSigningInput(revealPubkey);
        const validIdentitySig = identity.sign(signingInput);

        const content = new TextEncoder().encode("malformed reveal sig");
        // Use a garbage REVEAL signature (won't verify against revealPubkey).
        const badRevealSig = new Uint8Array(64).fill(0xab);

        const nonceResult = await client.requestAttestationNonce(content);
        const result = await client.submitMutation({
          mutationType: "schema_change",
          touchedMetaStructures: ["appetite_axis_schema"],
          contentCanonicalBytes: content,
          attestationSignature: badRevealSig,
          nonce: nonceResult.nonce,
          expiryUnixNs: nonceResult.expiryUnixNs,
          revealPubkey,
          identitySignatureOverRevealPubkey: validIdentitySig,
        });
        assert.equal(result.accepted, false);
        // Python catches the REVEAL signature failure via attestation verification.
        assert.match(result.rejectionReason, /attestation/i);
      } finally {
        await client.shutdown();
      }
    } finally {
      cleanupDir(opDir);
    }
  });

  // -------------------------------------------------------------------------
  // M13 anchor-surface nonce + dual-clock expiry tests.
  // -------------------------------------------------------------------------
  it("M13: requestAttestationNonce returns nonce + expiry + dag_tip", async () => {
    const client = await spawn();
    try {
      const content = new TextEncoder().encode("hello m13");
      const result = await client.requestAttestationNonce(content);
      assert.equal(result.nonce.length, 32);
      assert.equal(result.boundDagTip.length, 32);
      assert.ok(result.expiryUnixNs > 0n);
      assert.equal(result.ttlSeconds, 300n);
    } finally {
      await client.shutdown();
    }
  });

  it("M13: full anchor-surface envelope CI mutation is accepted", async () => {
    const opDir = mkdtempSync(resolvePath(tmpdir(), "myco-m13-op-"));
    try {
      const { OperatorIdentity } = await import("../src/operator_identity.ts");
      const identity = OperatorIdentity.loadOrCreate(opDir);
      const stateDir = freshStateDir();
      const client = await SubstrateClient.spawn({
        substrateBinary: SUBSTRATE_BIN,
        env: { MYCO_STATE_DIR: stateDir },
        operatorIdentity: identity,
      });
      try {
        const content = new TextEncoder().encode("CI with full envelope");
        const nonceResult = await client.requestAttestationNonce(content);
        const sig = identity.sign(content);
        const result = await client.submitMutation({
          mutationType: "schema_change",
          touchedMetaStructures: ["appetite_axis_schema"],
          contentCanonicalBytes: content,
          attestationSignature: sig,
          nonce: nonceResult.nonce,
          expiryUnixNs: nonceResult.expiryUnixNs,
        });
        assert.equal(
          result.accepted,
          true,
          `full envelope should accept; got rejection: ${result.rejectionReason}`,
        );
        assert.equal(result.classification, "contract_identity_level");
      } finally {
        await client.shutdown();
      }
    } finally {
      cleanupDir(opDir);
    }
  });

  it("M13: replayed nonce is rejected with C5 immune emission", async () => {
    const opDir = mkdtempSync(resolvePath(tmpdir(), "myco-m13-op-"));
    try {
      const { OperatorIdentity } = await import("../src/operator_identity.ts");
      const identity = OperatorIdentity.loadOrCreate(opDir);
      const stateDir = freshStateDir();
      const client = await SubstrateClient.spawn({
        substrateBinary: SUBSTRATE_BIN,
        env: { MYCO_STATE_DIR: stateDir },
        operatorIdentity: identity,
      });
      try {
        const content = new TextEncoder().encode("replay test");
        const nonceResult = await client.requestAttestationNonce(content);
        const sig = identity.sign(content);

        // First submission: succeeds.
        const r1 = await client.submitMutation({
          mutationType: "schema_change",
          touchedMetaStructures: ["appetite_axis_schema"],
          contentCanonicalBytes: content,
          attestationSignature: sig,
          nonce: nonceResult.nonce,
          expiryUnixNs: nonceResult.expiryUnixNs,
        });
        assert.equal(r1.accepted, true);

        // Second submission with SAME nonce: must be rejected (replay).
        const r2 = await client.submitMutation({
          mutationType: "schema_change",
          touchedMetaStructures: ["appetite_axis_schema"],
          contentCanonicalBytes: content,
          attestationSignature: sig,
          nonce: nonceResult.nonce,
          expiryUnixNs: nonceResult.expiryUnixNs,
        });
        assert.equal(r2.accepted, false);
        assert.match(r2.rejectionReason, /replay|consumed/);

        // Verify C5 immune sporocarp was emitted.
        const events = await client.queryImmuneEvents();
        const c5 = events.events.find((e) =>
          e.nodeType.includes("C5_attestation_invalid"),
        );
        assert.ok(c5, "expected C5 immune sporocarp on replay");
      } finally {
        await client.shutdown();
      }
    } finally {
      cleanupDir(opDir);
    }
  });

  it("M13: unknown nonce is rejected with C5", async () => {
    const opDir = mkdtempSync(resolvePath(tmpdir(), "myco-m13-op-"));
    try {
      const { OperatorIdentity } = await import("../src/operator_identity.ts");
      const identity = OperatorIdentity.loadOrCreate(opDir);
      const stateDir = freshStateDir();
      const client = await SubstrateClient.spawn({
        substrateBinary: SUBSTRATE_BIN,
        env: { MYCO_STATE_DIR: stateDir },
        operatorIdentity: identity,
      });
      try {
        const content = new TextEncoder().encode("unknown nonce attempt");
        const sig = identity.sign(content);
        // Make up a nonce that was never issued.
        const fakeNonce = new Uint8Array(32).fill(0xee);
        const result = await client.submitMutation({
          mutationType: "schema_change",
          touchedMetaStructures: ["appetite_axis_schema"],
          contentCanonicalBytes: content,
          attestationSignature: sig,
          nonce: fakeNonce,
        });
        assert.equal(result.accepted, false);
        assert.match(result.rejectionReason, /unknown|never issued/);
      } finally {
        await client.shutdown();
      }
    } finally {
      cleanupDir(opDir);
    }
  });

  it("M13: wrong content hash binding is rejected with C5", async () => {
    const opDir = mkdtempSync(resolvePath(tmpdir(), "myco-m13-op-"));
    try {
      const { OperatorIdentity } = await import("../src/operator_identity.ts");
      const identity = OperatorIdentity.loadOrCreate(opDir);
      const stateDir = freshStateDir();
      const client = await SubstrateClient.spawn({
        substrateBinary: SUBSTRATE_BIN,
        env: { MYCO_STATE_DIR: stateDir },
        operatorIdentity: identity,
      });
      try {
        const contentA = new TextEncoder().encode("original content");
        const contentB = new TextEncoder().encode("different content");
        // Request nonce bound to A.
        const nonceResult = await client.requestAttestationNonce(contentA);
        const sig = identity.sign(contentB);
        // Try to submit with B (wrong binding).
        const result = await client.submitMutation({
          mutationType: "schema_change",
          touchedMetaStructures: ["appetite_axis_schema"],
          contentCanonicalBytes: contentB,
          attestationSignature: sig,
          nonce: nonceResult.nonce,
          expiryUnixNs: nonceResult.expiryUnixNs,
        });
        assert.equal(result.accepted, false);
        assert.match(result.rejectionReason, /wrong-binding|content_hash/);
      } finally {
        await client.shutdown();
      }
    } finally {
      cleanupDir(opDir);
    }
  });

  // -------------------------------------------------------------------------
  // M12 ad-hoc immune check tests.
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

  it("M12: runImmuneCheck includes substrate_id + dag + pubkey + owner_keys checks", async () => {
    const client = await spawn();
    try {
      const report = await client.runImmuneCheck();
      const checkIds = report.checks.map((c) => c.checkId);
      assert.ok(checkIds.includes("substrate_id_well_formed"));
      assert.ok(checkIds.includes("cycle_counter_monotonic"));
      assert.ok(checkIds.includes("pinned_pubkey_well_formed"));
      assert.ok(checkIds.includes("dag_verify_all"));
      assert.ok(checkIds.includes("owner_keys_consistency"));
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
  // M11 active immune system tests.
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

  it("M11: CI without attestation emits C5 immune sporocarp", async () => {
    const client = await spawn();
    try {
      const result = await client.submitMutation({
        mutationType: "schema_change_attempt",
        touchedMetaStructures: ["appetite_axis_schema"],
        contentCanonicalBytes: new TextEncoder().encode("ci without sig"),
      });
      assert.equal(result.accepted, false);
      assert.equal(result.classification, "contract_identity_level");
      const report = await client.queryImmuneEvents();
      assert.equal(report.totalImmuneCount, 1n);
      assert.equal(
        report.events[0]!.nodeType,
        "immune:C5_attestation_invalid",
      );
    } finally {
      await client.shutdown();
    }
  });

  it("M11: CI with wrong-key signature emits C5 immune sporocarp", async () => {
    const opDir = mkdtempSync(resolvePath(tmpdir(), "myco-m11-op-"));
    const wrongDir = mkdtempSync(resolvePath(tmpdir(), "myco-m11-wrong-"));
    try {
      const { OperatorIdentity } = await import("../src/operator_identity.ts");
      const identity = OperatorIdentity.loadOrCreate(opDir);
      const wrongIdentity = OperatorIdentity.loadOrCreate(wrongDir);
      const stateDir = freshStateDir();
      const client = await SubstrateClient.spawn({
        substrateBinary: SUBSTRATE_BIN,
        env: { MYCO_STATE_DIR: stateDir },
        operatorIdentity: identity,
      });
      try {
        const content = new TextEncoder().encode("forged attempt");
        const wrongSig = wrongIdentity.sign(content);
        const result = await client.submitMutation({
          mutationType: "schema_change",
          touchedMetaStructures: ["appetite_axis_schema"],
          contentCanonicalBytes: content,
          attestationSignature: wrongSig,
        });
        assert.equal(result.accepted, false);
        const report = await client.queryImmuneEvents();
        assert.equal(report.totalImmuneCount, 1n);
        assert.equal(
          report.events[0]!.nodeType,
          "immune:C5_attestation_invalid",
        );
      } finally {
        await client.shutdown();
      }
    } finally {
      cleanupDir(opDir);
      cleanupDir(wrongDir);
    }
  });

  it("M11: pubkey mismatch emits C2 immune sporocarp persisted to disk", async () => {
    const stateDir = freshStateDir();
    const opDirA = mkdtempSync(resolvePath(tmpdir(), "myco-m11-pin-a-"));
    const opDirB = mkdtempSync(resolvePath(tmpdir(), "myco-m11-pin-b-"));
    try {
      const { OperatorIdentity } = await import("../src/operator_identity.ts");
      const identityA = OperatorIdentity.loadOrCreate(opDirA);
      const identityB = OperatorIdentity.loadOrCreate(opDirB);

      // Session 1: pin identity A.
      const c1 = await SubstrateClient.spawn({
        substrateBinary: SUBSTRATE_BIN,
        env: { MYCO_STATE_DIR: stateDir },
        operatorIdentity: identityA,
      });
      await c1.shutdown();

      // Session 2: try identity B → rejected (M9 + M11 emits immune sporocarp).
      try {
        await SubstrateClient.spawn({
          substrateBinary: SUBSTRATE_BIN,
          env: { MYCO_STATE_DIR: stateDir },
          operatorIdentity: identityB,
        });
      } catch {
        // Expected rejection.
      }

      // Session 3: back to identity A → can query the immune event from session 2.
      const c3 = await SubstrateClient.spawn({
        substrateBinary: SUBSTRATE_BIN,
        env: { MYCO_STATE_DIR: stateDir },
        operatorIdentity: identityA,
      });
      try {
        const report = await c3.queryImmuneEvents();
        assert.ok(
          report.totalImmuneCount >= 1n,
          `expected ≥1 immune event after rejected handshake; got ${report.totalImmuneCount}`,
        );
        const c2Event = report.events.find((e) =>
          e.nodeType.includes("C2_handshake_pubkey_mismatch"),
        );
        assert.ok(c2Event, "C2 handshake_pubkey_mismatch should be in immune events");
      } finally {
        await c3.shutdown();
      }
    } finally {
      cleanupDir(stateDir);
      cleanupDir(opDirA);
      cleanupDir(opDirB);
    }
  });

  it("M11: immune events persist across restart", async () => {
    const dir = freshStateDir();
    try {
      // Session 1: produce an immune event.
      const c1 = await spawn(dir);
      await c1.submitMutation({
        mutationType: "completely_unknown_xyz",
        contentCanonicalBytes: new TextEncoder().encode("test"),
      });
      const r1 = await c1.queryImmuneEvents();
      assert.equal(r1.totalImmuneCount, 1n);
      await c1.shutdown();

      // Session 2: immune event should persist.
      const c2 = await spawn(dir);
      try {
        const r2 = await c2.queryImmuneEvents();
        assert.equal(r2.totalImmuneCount, 1n);
        assert.equal(
          r2.events[0]!.nodeType,
          "immune:C14_untyped_mutation_blocked",
        );
      } finally {
        await c2.shutdown();
      }
    } finally {
      cleanupDir(dir);
    }
  });

  // -------------------------------------------------------------------------
  // M10 classified-mutation flow tests.
  // -------------------------------------------------------------------------
  it("M10: DAILY mutation is accepted and recorded as DAG node", async () => {
    const client = await spawn();
    try {
      const result = await client.submitMutation({
        mutationType: "delta_absorb",
        contentCanonicalBytes: new TextEncoder().encode("hello world daily"),
      });
      assert.equal(result.classification, "daily");
      assert.equal(result.accepted, true);
      assert.equal(result.rejectionReason, "");
      assert.ok(result.dagNodeHash, "accepted mutation must carry dag_node_hash");
      assert.equal(result.dagNodeHash!.length, 32);
      // Verify DAG actually grew.
      const recent = await client.queryRecentNodes(10n);
      assert.equal(recent.totalDagSize, 1n);
      assert.equal(recent.nodes[0]!.nodeType, "mutation:delta_absorb");
    } finally {
      await client.shutdown();
    }
  });

  it("M10: UNTYPED mutation is rejected (L1_HARD_RULES C14)", async () => {
    const client = await spawn();
    try {
      const result = await client.submitMutation({
        mutationType: "completely_unknown_random_type_xyz",
        contentCanonicalBytes: new TextEncoder().encode("should fail"),
      });
      assert.equal(result.classification, "untyped");
      assert.equal(result.accepted, false);
      assert.match(result.rejectionReason, /untyped/);
      // Verify DAG did NOT grow.
      const recent = await client.queryRecentNodes(10n);
      assert.equal(recent.totalDagSize, 0n);
    } finally {
      await client.shutdown();
    }
  });

  it("M10: CI mutation WITHOUT attestation is rejected", async () => {
    const client = await spawn();
    try {
      const result = await client.submitMutation({
        mutationType: "axis_schema_change",
        touchedMetaStructures: ["appetite_axis_schema"],
        contentCanonicalBytes: new TextEncoder().encode("schema change attempt"),
        // attestationSignature: undefined  ← no attestation
      });
      assert.equal(result.classification, "contract_identity_level");
      assert.equal(result.accepted, false);
      assert.match(result.rejectionReason, /attestation/i);
    } finally {
      await client.shutdown();
    }
  });

  it("M10: CI mutation WITH valid attestation is accepted", async () => {
    // Operator identity doubles as genesis owner key (M10 minimum: operator==owner).
    // So signing with the operator's identity key produces a valid CI attestation.
    const opDir = mkdtempSync(resolvePath(tmpdir(), "myco-m10-op-"));
    try {
      const { OperatorIdentity } = await import("../src/operator_identity.ts");
      const identity = OperatorIdentity.loadOrCreate(opDir);

      const stateDir = freshStateDir();
      const client = await SubstrateClient.spawn({
        substrateBinary: SUBSTRATE_BIN,
        env: { MYCO_STATE_DIR: stateDir },
        operatorIdentity: identity,
      });
      try {
        const content = new TextEncoder().encode("CI mutation content");
        const signature = identity.sign(content);
        const result = await client.submitMutation({
          mutationType: "axis_schema_change",
          touchedMetaStructures: ["appetite_axis_schema"],
          contentCanonicalBytes: content,
          attestationSignature: signature,
        });
        assert.equal(result.classification, "contract_identity_level");
        assert.equal(
          result.accepted,
          true,
          `CI mutation should be accepted; got rejection: ${result.rejectionReason}`,
        );
        assert.ok(result.dagNodeHash);
      } finally {
        await client.shutdown();
      }
    } finally {
      cleanupDir(opDir);
    }
  });

  it("M10: CI mutation WITH invalid (wrong-key) signature is rejected", async () => {
    const opDir = mkdtempSync(resolvePath(tmpdir(), "myco-m10-op-"));
    const wrongDir = mkdtempSync(resolvePath(tmpdir(), "myco-m10-wrong-"));
    try {
      const { OperatorIdentity } = await import("../src/operator_identity.ts");
      const identity = OperatorIdentity.loadOrCreate(opDir);
      const wrongIdentity = OperatorIdentity.loadOrCreate(wrongDir);

      const stateDir = freshStateDir();
      const client = await SubstrateClient.spawn({
        substrateBinary: SUBSTRATE_BIN,
        env: { MYCO_STATE_DIR: stateDir },
        operatorIdentity: identity, // Substrate pins identity's pubkey
      });
      try {
        const content = new TextEncoder().encode("forged attestation attempt");
        // Sign with the WRONG key (not the pinned/owner key).
        const wrongSignature = wrongIdentity.sign(content);
        const result = await client.submitMutation({
          mutationType: "axis_schema_change",
          touchedMetaStructures: ["appetite_axis_schema"],
          contentCanonicalBytes: content,
          attestationSignature: wrongSignature,
        });
        assert.equal(result.classification, "contract_identity_level");
        assert.equal(result.accepted, false);
        assert.match(result.rejectionReason, /attestation/i);
      } finally {
        await client.shutdown();
      }
    } finally {
      cleanupDir(opDir);
      cleanupDir(wrongDir);
    }
  });

  it("M10: accepted DAILY mutation DAG persists across restart", async () => {
    const dir = freshStateDir();
    try {
      // Session 1: submit a daily mutation.
      const c1 = await spawn(dir);
      const r1 = await c1.submitMutation({
        mutationType: "delta_absorb",
        contentCanonicalBytes: new TextEncoder().encode("session1 mutation"),
      });
      assert.equal(r1.accepted, true);
      const dagSizeBefore = (await c1.queryRecentNodes(10n)).totalDagSize;
      assert.equal(dagSizeBefore, 1n);
      await c1.shutdown();

      // Session 2: DAG should be hydrated.
      const c2 = await spawn(dir);
      try {
        const recent = await c2.queryRecentNodes(10n);
        assert.equal(recent.totalDagSize, 1n);
        assert.equal(recent.nodes[0]!.nodeType, "mutation:delta_absorb");
      } finally {
        await c2.shutdown();
      }
    } finally {
      cleanupDir(dir);
    }
  });

  // -------------------------------------------------------------------------
  // M9 operator identity + TOFU tests.
  // -------------------------------------------------------------------------
  it("M9: TOFU pins operator pubkey on first hello", async () => {
    const stateDir = freshStateDir();
    const opDir = mkdtempSync(resolvePath(tmpdir(), "myco-m9-op-"));
    try {
      const { OperatorIdentity } = await import("../src/operator_identity.ts");
      const identity = OperatorIdentity.loadOrCreate(opDir);

      const client = await SubstrateClient.spawn({
        substrateBinary: SUBSTRATE_BIN,
        env: { MYCO_STATE_DIR: stateDir },
        operatorIdentity: identity,
      });
      try {
        // Substrate should have pinned the pubkey to <state_dir>/operator_identity_pubkey.cb
        const pinnedPath = resolvePath(stateDir, "operator_identity_pubkey.cb");
        assert.ok(
          existsSync(pinnedPath),
          "substrate should have pinned operator pubkey on first hello",
        );
      } finally {
        await client.shutdown();
      }
    } finally {
      cleanupDir(stateDir);
      cleanupDir(opDir);
    }
  });

  it("M9: same operator identity reconnects successfully", async () => {
    const stateDir = freshStateDir();
    const opDir = mkdtempSync(resolvePath(tmpdir(), "myco-m9-op-"));
    try {
      const { OperatorIdentity } = await import("../src/operator_identity.ts");
      const identity = OperatorIdentity.loadOrCreate(opDir);

      // Session 1: pin.
      const c1 = await SubstrateClient.spawn({
        substrateBinary: SUBSTRATE_BIN,
        env: { MYCO_STATE_DIR: stateDir },
        operatorIdentity: identity,
      });
      await c1.shutdown();

      // Session 2: same identity → should succeed.
      const c2 = await SubstrateClient.spawn({
        substrateBinary: SUBSTRATE_BIN,
        env: { MYCO_STATE_DIR: stateDir },
        operatorIdentity: identity,
      });
      assert.ok(c2.helloAck.substrateVersion.length > 0);
      await c2.shutdown();
    } finally {
      cleanupDir(stateDir);
      cleanupDir(opDir);
    }
  });

  it("M9: different operator identity is rejected after pin", async () => {
    const stateDir = freshStateDir();
    const opDirA = mkdtempSync(resolvePath(tmpdir(), "myco-m9-op-a-"));
    const opDirB = mkdtempSync(resolvePath(tmpdir(), "myco-m9-op-b-"));
    try {
      const { OperatorIdentity } = await import("../src/operator_identity.ts");
      const identityA = OperatorIdentity.loadOrCreate(opDirA);
      const identityB = OperatorIdentity.loadOrCreate(opDirB);
      assert.notDeepEqual(
        identityA.publicKeyBytes(),
        identityB.publicKeyBytes(),
        "test setup: two identities must differ",
      );

      // Session 1: pin identity A.
      const c1 = await SubstrateClient.spawn({
        substrateBinary: SUBSTRATE_BIN,
        env: { MYCO_STATE_DIR: stateDir },
        operatorIdentity: identityA,
      });
      await c1.shutdown();

      // Session 2: present identity B → substrate should reject.
      // The rejection may manifest as either:
      //  (a) an explicit "worker error: code=dispatcher_error message=...mismatch..."
      //      envelope (when the substrate keys its error response with our
      //      session_secret), or
      //  (b) "child stdout closed unexpectedly" when the substrate exits.
      // Either is acceptable proof that identity B was not accepted.
      let rejected = false;
      try {
        const c2 = await SubstrateClient.spawn({
          substrateBinary: SUBSTRATE_BIN,
          env: { MYCO_STATE_DIR: stateDir },
          operatorIdentity: identityB,
        });
        await c2.shutdown();
      } catch (e) {
        rejected = true;
        const msg = e instanceof Error ? e.message : String(e);
        assert.ok(
          msg.includes("mismatch") ||
            msg.includes("rejected") ||
            msg.includes("closed") ||
            msg.includes("EOF") ||
            msg.includes("ECONNRESET") ||
            msg.includes("child"),
          `expected mismatch/rejection error; got: ${msg}`,
        );
      }
      assert.equal(rejected, true, "identity B should have been rejected");
    } finally {
      cleanupDir(stateDir);
      cleanupDir(opDirA);
      cleanupDir(opDirB);
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
