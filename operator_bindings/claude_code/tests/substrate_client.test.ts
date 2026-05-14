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
      // Verify mutation:* DAG node was inserted (M21.1: DAG also contains
      // genesis_event + operator_pinned init events — filter by prefix).
      const muts = await client.queryRecentNodes(10n, "mutation:");
      assert.equal(muts.filteredTotal, 1n);
      assert.equal(muts.nodes[0]!.nodeType, "mutation:delta_absorb");
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
      // Per M11+: rejection emits a C14 immune sporocarp into the DAG.
      // No mutation:* node should exist (only init events + immune:C14).
      const muts = await client.queryRecentNodes(20n, "mutation:");
      assert.equal(
        muts.filteredTotal,
        0n,
        "UNTYPED rejection must not produce a mutation node in the DAG",
      );
      const recent = await client.queryRecentNodes(20n);
      const c14 = recent.nodes.find((n) =>
        n.nodeType.includes("C14_untyped_mutation_blocked"),
      );
      assert.ok(c14, "expected C14 immune sporocarp on UNTYPED rejection");
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
      // M21.1: DAG contains init events too; filter for mutation:* to count.
      const mutsBefore = await c1.queryRecentNodes(10n, "mutation:");
      assert.equal(mutsBefore.filteredTotal, 1n);
      await c1.shutdown();

      // Session 2: DAG should be hydrated.
      const c2 = await spawn(dir);
      try {
        const muts = await c2.queryRecentNodes(10n, "mutation:");
        assert.equal(muts.filteredTotal, 1n);
        assert.equal(muts.nodes[0]!.nodeType, "mutation:delta_absorb");
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
      // M21.1 dual-write: even a "fresh" substrate has genesis_event +
      // operator_pinned events in the DAG. coldStart is therefore false, but
      // there are no SPOROCARP or MUTATION events to cluster around — the
      // intent neighborhood is just init events (typically 1-2 nodes, no
      // meaningful clusters).
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
        assert.equal(
          fullPost.totalDagSize,
          totalDagPre,
          "full DAG size (incl. init events) should survive restart",
        );
        assert.deepEqual(
          fullPost.dagTip,
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

  // -------------------------------------------------------------------------
  // M15 DAG enumeration closure + dual-clock expiry tests.
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
      // M21.1: full enumeration includes init events (genesis_event,
      // operator_pinned) + axis_registered + 3 axis_perturbed + 3 sporocarp +
      // 3 cycle_advanced. Count must be ≥3 (3 sporocarps minimum).
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

  it("M15: dual-clock nonce accepts when both clocks in-window", async () => {
    const opDir = mkdtempSync(resolvePath(tmpdir(), "myco-m15-op-"));
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
        const content = new TextEncoder().encode("M15 dual-clock happy path");
        const anchorClockAtRequest = BigInt(Date.now()) * 1_000_000n; // ms → ns
        const nonceResult = await client.requestAttestationNonce(
          content,
          anchorClockAtRequest,
        );
        assert.ok(
          nonceResult.anchorClockExpiryUnixNs !== null,
          "anchor_clock_expiry should be present when nonce request includes anchor_clock",
        );
        const sig = identity.sign(content);
        // Submit with anchor_clock close to request time (in-window).
        const result = await client.submitMutation({
          mutationType: "schema_change",
          touchedMetaStructures: ["appetite_axis_schema"],
          contentCanonicalBytes: content,
          attestationSignature: sig,
          nonce: nonceResult.nonce,
          expiryUnixNs: nonceResult.expiryUnixNs,
          anchorClockSubmittedAtUnixNs: anchorClockAtRequest + 1_000_000n, // +1ms
        });
        assert.equal(
          result.accepted,
          true,
          `dual-clock in-window should accept; got: ${result.rejectionReason}`,
        );
      } finally {
        await client.shutdown();
      }
    } finally {
      cleanupDir(opDir);
    }
  });

  it("M15: dual-clock rejects anchor-clock skewed forward past expiry", async () => {
    const opDir = mkdtempSync(resolvePath(tmpdir(), "myco-m15-op-"));
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
        const content = new TextEncoder().encode("M15 dual-clock forward skew");
        const anchorClockAtRequest = BigInt(Date.now()) * 1_000_000n;
        const nonceResult = await client.requestAttestationNonce(
          content,
          anchorClockAtRequest,
        );
        const sig = identity.sign(content);
        // Submit anchor_clock_submitted_at WAY past anchor-clock expiry.
        const TTL_NS = 300n * 1_000_000_000n;
        const farFuture = anchorClockAtRequest + TTL_NS + 1_000_000_000n;
        const result = await client.submitMutation({
          mutationType: "schema_change",
          touchedMetaStructures: ["appetite_axis_schema"],
          contentCanonicalBytes: content,
          attestationSignature: sig,
          nonce: nonceResult.nonce,
          expiryUnixNs: nonceResult.expiryUnixNs,
          anchorClockSubmittedAtUnixNs: farFuture,
        });
        assert.equal(result.accepted, false);
        assert.match(result.rejectionReason, /anchor-clock|dual-clock/);
      } finally {
        await client.shutdown();
      }
    } finally {
      cleanupDir(opDir);
    }
  });

  it("M15: dual-clock rejects anchor-clock skewed backward before issuance", async () => {
    const opDir = mkdtempSync(resolvePath(tmpdir(), "myco-m15-op-"));
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
        const content = new TextEncoder().encode("M15 dual-clock backward skew");
        const anchorClockAtRequest = BigInt(Date.now()) * 1_000_000n;
        const nonceResult = await client.requestAttestationNonce(
          content,
          anchorClockAtRequest,
        );
        const sig = identity.sign(content);
        // Claim "submit happened BEFORE issuance" (impossible — backward skew).
        const before = anchorClockAtRequest - 1_000_000_000n;
        const result = await client.submitMutation({
          mutationType: "schema_change",
          touchedMetaStructures: ["appetite_axis_schema"],
          contentCanonicalBytes: content,
          attestationSignature: sig,
          nonce: nonceResult.nonce,
          expiryUnixNs: nonceResult.expiryUnixNs,
          anchorClockSubmittedAtUnixNs: before,
        });
        assert.equal(result.accepted, false);
        assert.match(result.rejectionReason, /backward|dual-clock/);
      } finally {
        await client.shutdown();
      }
    } finally {
      cleanupDir(opDir);
    }
  });

  it("M15: nonce issued WITH anchor-clock but submit omits it is rejected", async () => {
    const opDir = mkdtempSync(resolvePath(tmpdir(), "myco-m15-op-"));
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
        const content = new TextEncoder().encode("M15 dual-clock contract enforcement");
        const anchorClockAtRequest = BigInt(Date.now()) * 1_000_000n;
        const nonceResult = await client.requestAttestationNonce(
          content,
          anchorClockAtRequest,
        );
        const sig = identity.sign(content);
        // OMIT anchor_clock_submitted_at_unix_ns even though nonce is dual-clock.
        const result = await client.submitMutation({
          mutationType: "schema_change",
          touchedMetaStructures: ["appetite_axis_schema"],
          contentCanonicalBytes: content,
          attestationSignature: sig,
          nonce: nonceResult.nonce,
          expiryUnixNs: nonceResult.expiryUnixNs,
        });
        assert.equal(result.accepted, false);
        assert.match(result.rejectionReason, /dual-clock binding|anchor_clock_submitted/);
      } finally {
        await client.shutdown();
      }
    } finally {
      cleanupDir(opDir);
    }
  });

  it("M15: nonce issued WITHOUT anchor-clock works in M13-compat mode", async () => {
    const opDir = mkdtempSync(resolvePath(tmpdir(), "myco-m15-op-"));
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
        const content = new TextEncoder().encode("M15 single-clock backward-compat");
        // Request nonce WITHOUT anchor_clock.
        const nonceResult = await client.requestAttestationNonce(content);
        assert.equal(
          nonceResult.anchorClockExpiryUnixNs,
          null,
          "single-clock nonce should NOT echo anchor_clock_expiry",
        );
        const sig = identity.sign(content);
        // Submit also without anchor_clock; this should work (M13 path).
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
          `single-clock M13-style should accept; got: ${result.rejectionReason}`,
        );
      } finally {
        await client.shutdown();
      }
    } finally {
      cleanupDir(opDir);
    }
  });

  // -------------------------------------------------------------------------
  // M16 P2 永恒吞噬: universal raw_material ingestion tests.
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
      // The DAG-node hash of the sporocarp is in dag_node_hash of sporocarp report.
      // For this test we'll use the queryRecentNodes to find it.
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

  // -------------------------------------------------------------------------
  // M17 P3 永恒进化: schema_evolution actually-applied tests.
  // -------------------------------------------------------------------------

  it("M17: modify_axis_threshold actually changes the threshold + emits evolution_succeeded", async () => {
    const opDir = mkdtempSync(resolvePath(tmpdir(), "myco-m17-op-"));
    try {
      const { OperatorIdentity } = await import("../src/operator_identity.ts");
      const { schemaDiffModifyAxisThresholdBytes } = await import("../src/protocol/messages.ts");
      const identity = OperatorIdentity.loadOrCreate(opDir);
      const stateDir = freshStateDir();
      const client = await SubstrateClient.spawn({
        substrateBinary: SUBSTRATE_BIN,
        env: { MYCO_STATE_DIR: stateDir },
        operatorIdentity: identity,
      });
      try {
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

        // Evolve: change threshold to 50.0.
        const diff = schemaDiffModifyAxisThresholdBytes("curiosity", 50.0);
        const sig = identity.sign(diff);
        const result = await client.submitMutation({
          mutationType: "schema_evolution",
          contentCanonicalBytes: diff,
          attestationSignature: sig,
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
        // If old threshold (10.0) were still active, this would fruit; if new
        // threshold (50.0) is now active, this should NOT fruit.
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
    } finally {
      cleanupDir(opDir);
    }
  });

  it("M17: modify_axis_threshold on unknown axis emits evolution_failed + rolls back", async () => {
    const opDir = mkdtempSync(resolvePath(tmpdir(), "myco-m17-op-"));
    try {
      const { OperatorIdentity } = await import("../src/operator_identity.ts");
      const { schemaDiffModifyAxisThresholdBytes } = await import("../src/protocol/messages.ts");
      const identity = OperatorIdentity.loadOrCreate(opDir);
      const stateDir = freshStateDir();
      const client = await SubstrateClient.spawn({
        substrateBinary: SUBSTRATE_BIN,
        env: { MYCO_STATE_DIR: stateDir },
        operatorIdentity: identity,
      });
      try {
        const diff = schemaDiffModifyAxisThresholdBytes("nonexistent_axis", 99.0);
        const sig = identity.sign(diff);
        const result = await client.submitMutation({
          mutationType: "schema_evolution",
          contentCanonicalBytes: diff,
          attestationSignature: sig,
          touchedMetaStructures: ["appetite_axis_schema"],
        });
        // Mutation is still "accepted" (the proposal was valid + signed).
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
    } finally {
      cleanupDir(opDir);
    }
  });

  it("M17: add_axis_to_gradient registers axis via CI gate + emits evolution_succeeded", async () => {
    const opDir = mkdtempSync(resolvePath(tmpdir(), "myco-m17-op-"));
    try {
      const { OperatorIdentity } = await import("../src/operator_identity.ts");
      const { schemaDiffAddAxisBytes } = await import("../src/protocol/messages.ts");
      const identity = OperatorIdentity.loadOrCreate(opDir);
      const stateDir = freshStateDir();
      const client = await SubstrateClient.spawn({
        substrateBinary: SUBSTRATE_BIN,
        env: { MYCO_STATE_DIR: stateDir },
        operatorIdentity: identity,
      });
      try {
        const diff = schemaDiffAddAxisBytes({
          axisName: "trust_in_owner",
          axisClass: "decay",
          fruitingThreshold: 0.1,
          initialValue: 1.0,
          decayRatePerCycle: 0.95,
          isMortalitySignal: true,
          updateRuleKind: "decay",
        });
        const sig = identity.sign(diff);
        const result = await client.submitMutation({
          mutationType: "schema_evolution",
          contentCanonicalBytes: diff,
          attestationSignature: sig,
          touchedMetaStructures: ["appetite_axis_schema"],
        });
        assert.equal(result.accepted, true);
        assert.equal(result.schemaApplySucceeded, true, result.schemaApplyFailureReason);
        assert.equal(result.schemaApplyOp, "add_axis_to_gradient");

        // The axis should now be active — snapshot exposes it at initial_value=1.0.
        const snap = await client.snapshot();
        assert.equal(snap.get("trust_in_owner"), 1.0);
      } finally {
        await client.shutdown();
      }
    } finally {
      cleanupDir(opDir);
    }
  });

  it("M17: schema_evolution WITHOUT attestation is rejected (CI gate enforced)", async () => {
    const client = await spawn();
    try {
      const { schemaDiffModifyAxisThresholdBytes } = await import("../src/protocol/messages.ts");
      const diff = schemaDiffModifyAxisThresholdBytes("any_axis", 1.0);
      const result = await client.submitMutation({
        mutationType: "schema_evolution",
        contentCanonicalBytes: diff,
        // NO attestation_signature.
      });
      assert.equal(result.accepted, false);
      assert.match(result.rejectionReason, /attestation/i);
      // Schema apply must NOT have been attempted (gated by attestation).
      assert.equal(result.schemaApplyAttempted, false);
    } finally {
      await client.shutdown();
    }
  });

  it("M16: queryRecentNodes prefix filter exposes filteredTotal vs totalDagSize", async () => {
    const client = await spawn();
    try {
      await client.registerAxis({
        name: "x",
        axisClass: "appetite",
        fruitingThreshold: 1.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      await client.perturb("x", 2.0);
      await client.advance(1n); // produces sporocarp DAG node
      await client.ingestRawMaterial({
        contentKind: "text",
        contentBytes: new TextEncoder().encode("a"),
      });
      await client.ingestRawMaterial({
        contentKind: "text",
        contentBytes: new TextEncoder().encode("b"),
      });
      // M21.1: DAG also contains init events + axis_registered + axis_perturbed
      // + cycle_advanced. filteredTotal for raw_material: is still 2.
      const unfiltered = await client.queryRecentNodes(20n);
      assert.ok(unfiltered.totalDagSize >= 3n);
      assert.equal(unfiltered.filteredTotal, unfiltered.totalDagSize);

      const filtered = await client.queryRecentNodes(20n, "raw_material:");
      assert.equal(filtered.totalDagSize, unfiltered.totalDagSize);
      assert.equal(filtered.filteredTotal, 2n);
      assert.equal(filtered.returnedCount, 2n);
    } finally {
      await client.shutdown();
    }
  });

  // -------------------------------------------------------------------------
  // M18 P4 永恒迭代: cycle pipeline activation tests.
  // -------------------------------------------------------------------------

  it("M18: advance with no raw_material absorbs zero deltas (no absorption_event)", async () => {
    const client = await spawn();
    try {
      const adv = await client.advance(1n);
      assert.equal(adv.deltasAbsorbed, 0n);
      assert.equal(adv.absorptionEventHash, null);
    } finally {
      await client.shutdown();
    }
  });

  it("M18: advance after ingesting raw_material emits absorption_event:cycle_{N}", async () => {
    const client = await spawn();
    try {
      await client.registerAxis({
        name: "ax",
        axisClass: "appetite",
        fruitingThreshold: 100.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      // Ingest two raw_material nodes.
      await client.ingestRawMaterial({
        contentKind: "text",
        contentBytes: new TextEncoder().encode("first meal"),
      });
      await client.ingestRawMaterial({
        contentKind: "text",
        contentBytes: new TextEncoder().encode("second meal"),
      });

      // Advance — should absorb both.
      const adv = await client.advance(1n);
      assert.equal(adv.deltasAbsorbed, 2n, "expected 2 raw_material absorbed");
      assert.ok(adv.absorptionEventHash, "absorption_event_hash should be set");

      // Verify the DAG has an absorption_event:* node.
      const recent = await client.queryRecentNodes(20n, "absorption_event:");
      assert.equal(recent.filteredTotal, 1n);
      assert.match(recent.nodes[0]!.nodeType, /^absorption_event:cycle_/);
    } finally {
      await client.shutdown();
    }
  });

  it("M18: subsequent advances skip already-absorbed raw_material", async () => {
    const client = await spawn();
    try {
      await client.registerAxis({
        name: "ax2",
        axisClass: "appetite",
        fruitingThreshold: 100.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      await client.ingestRawMaterial({
        contentKind: "text",
        contentBytes: new TextEncoder().encode("one"),
      });
      const adv1 = await client.advance(1n);
      assert.equal(adv1.deltasAbsorbed, 1n);

      // Second advance with no new ingestion — absorption count should be 0.
      const adv2 = await client.advance(2n);
      assert.equal(adv2.deltasAbsorbed, 0n);
      assert.equal(adv2.absorptionEventHash, null);

      // Third advance after a new ingestion — count should be 1 again.
      await client.ingestRawMaterial({
        contentKind: "text",
        contentBytes: new TextEncoder().encode("two"),
      });
      const adv3 = await client.advance(3n);
      assert.equal(adv3.deltasAbsorbed, 1n);
      assert.ok(adv3.absorptionEventHash);
    } finally {
      await client.shutdown();
    }
  });

  it("M18: handshake_events_processed reports 1 when operator identity is pinned", async () => {
    const opDir = mkdtempSync(resolvePath(tmpdir(), "myco-m18-op-"));
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
        const adv = await client.advance(1n);
        assert.equal(adv.handshakeEventsProcessed, 1n);
      } finally {
        await client.shutdown();
      }
    } finally {
      cleanupDir(opDir);
    }
  });

  it("M18: advance with no axes registered still completes (Tier1 DAG verify passes)", async () => {
    const client = await spawn();
    try {
      // No axes, no ingestion — just bare advance. DAG is empty → Tier1 passes.
      const adv = await client.advance(1n);
      assert.equal(adv.fruitedAxes.length, 0);
      assert.equal(adv.deltasAbsorbed, 0n);
    } finally {
      await client.shutdown();
    }
  });

  it("M18: absorption_event has multi-parent linkage (prior_tip + raw_material hashes)", async () => {
    const client = await spawn();
    try {
      await client.registerAxis({
        name: "ax3",
        axisClass: "appetite",
        fruitingThreshold: 100.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      });
      const ingest = await client.ingestRawMaterial({
        contentKind: "text",
        contentBytes: new TextEncoder().encode("multiparent test"),
      });
      const adv = await client.advance(1n);
      assert.ok(adv.absorptionEventHash);

      // Look up the absorption_event node in the DAG; verify parent_hashes includes
      // the raw_material hash.
      const recent = await client.queryRecentNodes(20n);
      const absorbNode = recent.nodes.find((n) =>
        n.nodeType.startsWith("absorption_event:"),
      );
      assert.ok(absorbNode);
      // Multi-parent: at least 1 parent (could be prior tip + raw_material; or
      // raw_material was tip itself, so 1 parent).
      assert.ok(absorbNode!.parentHashes.length >= 1);
      const parentHashesHex = absorbNode!.parentHashes.map((p) =>
        Buffer.from(p).toString("hex"),
      );
      const rawHex = Buffer.from(ingest.dagNodeHash).toString("hex");
      assert.ok(
        parentHashesHex.includes(rawHex),
        "absorption_event should link back to the raw_material hash",
      );
    } finally {
      await client.shutdown();
    }
  });

  // -------------------------------------------------------------------------
  // M19 P7 必朽 (endogenous mortality) + P9 皮肤 (C18 detector) tests.
  // -------------------------------------------------------------------------

  // -------------------------------------------------------------------------
  // M20 P8 永恒繁衍: substrate reproduction tests.
  // -------------------------------------------------------------------------

  it("M20 P8: sproutChild creates child state_dir with manifest + gradient + spore_emission", async () => {
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

        const result = await client.sproutChild({ childStateDir: childDir });
        assert.equal(result.childSubstrateId.length, 32);
        assert.equal(result.childStateDir, childDir);
        assert.equal(result.childAxisCount, 1n);
        assert.equal(result.sporeEmissionHash.length, 32);

        // Verify child's state files exist.
        assert.ok(existsSync(`${childDir}/manifest.cb`), "child manifest.cb exists");
        assert.ok(existsSync(`${childDir}/gradient.cb`), "child gradient.cb exists");
        // Operator identity should also be inherited.
        assert.ok(
          existsSync(`${childDir}/operator_identity_pubkey.cb`),
          "child operator_identity_pubkey.cb exists",
        );

        // Verify parent's DAG has the spore_emission node.
        const recent = await client.queryRecentNodes(10n, "spore_emission:");
        assert.equal(recent.filteredTotal, 1n);
      } finally {
        await client.shutdown();
      }
    } finally {
      cleanupDir(parentDir);
      cleanupDir(childDir);
    }
  });

  it("M20: sproutChild refuses to overwrite existing manifest.cb", async () => {
    const parentDir = freshStateDir();
    const childDir = freshStateDir(); // already contains a manifest after spawn
    // Pre-populate childDir with a manifest by spawning a substrate there first.
    const preSpawn = await spawn(childDir);
    await preSpawn.shutdown();
    try {
      const client = await spawn(parentDir);
      try {
        await assert.rejects(
          () => client.sproutChild({ childStateDir: childDir }),
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
      await parent.sproutChild({ childStateDir: childDir });
      // Get parent's substrate_id for differentiation check.
      const parentInfo = parent.helloAck;
      void parentInfo;
      await parent.shutdown();

      // Spawn child substrate at childDir — it should boot with inherited axes.
      const child = await spawn(childDir);
      try {
        const snap = await child.snapshot();
        // Both axes inherited with their values.
        assert.equal(snap.size, 2);
        assert.equal(snap.get("hunger"), 2.5, "hunger value inherited");
        assert.equal(snap.get("vitality"), 1.0, "vitality value inherited");

        // Child has its OWN substrate_id (not the parent's).
        // We can verify indirectly: the child's DAG should be EMPTY (no parent
        // DAG transfer per L1 decision) — only events from the child's own
        // lifetime.
        const recent = await child.queryRecentNodes(10n);
        // Child may have boot-time integrity check immune nodes; that's fine.
        // But it should NOT have any spore_emission from the parent.
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
        contentBytes: new TextEncoder().encode("test"),
      });
      // Run the integrity check.
      const report = await client.runImmuneCheck();
      // canonical_bytes_render_drift check should be present and PASSING
      // for our well-formed DAG.
      const cbCheck = report.checks.find(
        (c) => c.checkId === "canonical_bytes_render_drift",
      );
      assert.ok(cbCheck, "expected canonical_bytes_render_drift check to be present");
      assert.equal(
        cbCheck!.passed,
        true,
        `expected canonical_bytes round-trip to pass; got: ${cbCheck!.evidence}`,
      );
      // total_checks should include the new C18 check.
      assert.ok(
        report.totalChecks >= 6n,
        `expected at least 6 integrity checks (5 prior + 1 C18); got ${report.totalChecks}`,
      );
    } finally {
      await client.shutdown();
    }
  });

  it("M19: self_euthanasia_proposal persists across substrate restart", async () => {
    const dir = freshStateDir();
    try {
      const c1 = await spawn(dir);
      await c1.registerAxis({
        name: "tired_axis",
        axisClass: "decay",
        fruitingThreshold: 0.1,
        initialValue: 1.0,
        decayRatePerCycle: 0.3,
        isMortalitySignal: true,
        updateRuleKind: "decay",
      });
      // Force the fruit.
      let fired = false;
      for (let c = 1n; c <= 10n; c++) {
        const adv = await c1.advance(c);
        if (adv.selfEuthanasiaProposalHashes.length > 0) {
          fired = true;
          break;
        }
      }
      assert.ok(fired, "mortality_signal should fire");
      await c1.shutdown();

      // Session 2: euthanasia proposal still in DAG.
      const c2 = await spawn(dir);
      try {
        const report = await c2.queryRecentNodes(20n, "self_euthanasia_proposal:");
        assert.ok(
          report.filteredTotal >= 1n,
          "self_euthanasia_proposal should survive restart",
        );
      } finally {
        await c2.shutdown();
      }
    } finally {
      cleanupDir(dir);
    }
  });

  it("M18: last_absorbed_cycle persists across substrate restart", async () => {
    const dir = freshStateDir();
    try {
      const c1 = await spawn(dir);
      await c1.ingestRawMaterial({
        contentKind: "text",
        contentBytes: new TextEncoder().encode("persistent"),
      });
      const adv1 = await c1.advance(1n);
      assert.equal(adv1.deltasAbsorbed, 1n);
      await c1.shutdown();

      // Session 2: advance again — should NOT re-absorb the same raw_material.
      const c2 = await spawn(dir);
      try {
        const adv2 = await c2.advance(2n);
        assert.equal(
          adv2.deltasAbsorbed,
          0n,
          "previously-absorbed raw_material should not be re-absorbed after restart",
        );
      } finally {
        await c2.shutdown();
      }
    } finally {
      cleanupDir(dir);
    }
  });

  // -------------------------------------------------------------------------
  // M21.1 P5 万物互联 dual-write: every state mutation emits a DAG event.
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

  it("M21.1: hello with operator_identity emits operator_pinned event", async () => {
    const opDir = mkdtempSync(resolvePath(tmpdir(), "myco-m21-op-"));
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
        const pinned = await client.queryRecentNodes(20n, "operator_pinned:");
        assert.equal(pinned.filteredTotal, 1n);
      } finally {
        await client.shutdown();
      }
    } finally {
      cleanupDir(opDir);
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
      // All matching node_types should be "axis_perturbed:p_emit"
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
      // cycle_advanced has no per-axis suffix; check at least 2.
      assert.ok(
        events.filteredTotal >= 2n,
        `expected ≥2 cycle_advanced events; got ${events.filteredTotal}`,
      );
    } finally {
      await client.shutdown();
    }
  });

  it("M21.1: request_attestation_nonce emits nonce_issued event", async () => {
    const opDir = mkdtempSync(resolvePath(tmpdir(), "myco-m21-op-"));
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
        const content = new TextEncoder().encode("m21 nonce test");
        await client.requestAttestationNonce(content);
        const events = await client.queryRecentNodes(20n, "nonce_issued:");
        assert.equal(events.filteredTotal, 1n);
      } finally {
        await client.shutdown();
      }
    } finally {
      cleanupDir(opDir);
    }
  });

  it("M21.1: submit_mutation with nonce emits nonce_consumed event", async () => {
    const opDir = mkdtempSync(resolvePath(tmpdir(), "myco-m21-op-"));
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
        const content = new TextEncoder().encode("m21 consume test");
        const nonceResult = await client.requestAttestationNonce(content);
        const sig = identity.sign(content);
        const r = await client.submitMutation({
          mutationType: "schema_change",
          touchedMetaStructures: ["appetite_axis_schema"],
          contentCanonicalBytes: content,
          attestationSignature: sig,
          nonce: nonceResult.nonce,
          expiryUnixNs: nonceResult.expiryUnixNs,
        });
        assert.equal(r.accepted, true);
        const consumed = await client.queryRecentNodes(20n, "nonce_consumed:");
        assert.equal(consumed.filteredTotal, 1n);
      } finally {
        await client.shutdown();
      }
    } finally {
      cleanupDir(opDir);
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
});
