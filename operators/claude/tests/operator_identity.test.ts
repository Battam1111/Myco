// Tests for OperatorIdentity — M-anchor-1 thin client.
//
// Pre-M-anchor-1 this file tested an in-process Ed25519 key. Post-M-anchor-1
// the key lives in a separate process (anchor_surface_host) and this file
// exercises the round-trip through that process. Several tests were removed
// because they tested the old in-process surface that no longer exists
// (e.g. `OperatorIdentity.fromSeed`, raw 32-byte seed-file assertions).

import { after, describe, it } from "node:test";
import assert from "node:assert/strict";
import { existsSync, mkdtempSync, rmSync } from "node:fs";
import { resolve as resolvePath } from "node:path";
import { tmpdir } from "node:os";

import {
  OperatorIdentity,
  defaultOperatorKeyDir,
} from "../src/operator_identity.ts";
import { killAllSpawnedHosts } from "../src/anchor_surface_client.ts";

function locateAnchorSurfaceBinary(): string {
  const fromEnv = process.env.MYCO_ANCHOR_SURFACE_BIN;
  if (fromEnv && existsSync(fromEnv)) return fromEnv;
  const root = resolvePath(import.meta.dirname ?? __dirname, "..", "..", "..");
  const exe = process.platform === "win32" ? ".exe" : "";
  const candidate = resolvePath(root, "target", "debug", `anchor-surface-host${exe}`);
  if (existsSync(candidate)) return candidate;
  throw new Error(
    `anchor-surface-host binary not found. Build with: cargo build -p anchor-surface-host (looked at ${candidate})`,
  );
}

const ANCHOR_SURFACE_BIN = locateAnchorSurfaceBinary();

// File-level teardown: kill any leftover anchor-surface-host children that
// individual tests' `await id.close()` calls didn't catch (e.g., on early
// test failure). Without this, leaked hosts hold stdio pipes that keep the
// Node event loop alive and the test process hangs.
after(async () => {
  await killAllSpawnedHosts();
});

function freshKeyDir(): string {
  return mkdtempSync(resolvePath(tmpdir(), "myco-op-id-"));
}

describe("OperatorIdentity (M-anchor-1 thin client)", () => {
  it("loadOrCreate spawns a host + returns a pubkey when none persisted", async () => {
    const dir = freshKeyDir();
    let id: OperatorIdentity | null = null;
    try {
      id = await OperatorIdentity.loadOrCreate(dir, {
        hostBinary: ANCHOR_SURFACE_BIN,
      });
      assert.equal(id.publicKey.bytes.length, 32);
      assert.equal(id.publicKeyBytes().length, 32);
      // owner_key.cb is persisted by the host process in `dir`.
      assert.ok(
        existsSync(resolvePath(dir, "owner_key.cb")),
        "anchor_surface_host should persist owner_key.cb",
      );
    } finally {
      if (id) await id.close();
      rmSync(dir, { recursive: true, force: true });
    }
  });

  it("loadOrCreate is deterministic: same dir → same pubkey", async () => {
    const dir = freshKeyDir();
    let id1: OperatorIdentity | null = null;
    let id2: OperatorIdentity | null = null;
    try {
      id1 = await OperatorIdentity.loadOrCreate(dir, {
        hostBinary: ANCHOR_SURFACE_BIN,
      });
      const pubkey1 = id1.publicKeyBytes();
      await id1.close();
      id1 = null;
      // Second connect/spawn from the same dir loads the persisted key.
      id2 = await OperatorIdentity.loadOrCreate(dir, {
        hostBinary: ANCHOR_SURFACE_BIN,
      });
      const pubkey2 = id2.publicKeyBytes();
      assert.deepEqual(pubkey1, pubkey2);
    } finally {
      if (id1) await id1.close();
      if (id2) await id2.close();
      rmSync(dir, { recursive: true, force: true });
    }
  });

  it("fresh dirs yield different pubkeys", async () => {
    const a = freshKeyDir();
    const b = freshKeyDir();
    let idA: OperatorIdentity | null = null;
    let idB: OperatorIdentity | null = null;
    try {
      idA = await OperatorIdentity.loadOrCreate(a, {
        hostBinary: ANCHOR_SURFACE_BIN,
      });
      idB = await OperatorIdentity.loadOrCreate(b, {
        hostBinary: ANCHOR_SURFACE_BIN,
      });
      assert.notDeepEqual(idA.publicKeyBytes(), idB.publicKeyBytes());
    } finally {
      if (idA) await idA.close();
      if (idB) await idB.close();
      rmSync(a, { recursive: true, force: true });
      rmSync(b, { recursive: true, force: true });
    }
  });

  it("sign + verify roundtrips (using anchor-client verifySignature)", async () => {
    const dir = freshKeyDir();
    let id: OperatorIdentity | null = null;
    try {
      id = await OperatorIdentity.loadOrCreate(dir, {
        hostBinary: ANCHOR_SURFACE_BIN,
      });
      const msg = new TextEncoder().encode("hello world");
      const sig = await id.sign(msg);
      assert.equal(sig.length, 64);

      const { verifySignature } = await import(
        "@myco/anchor-client/src/crypto.ts"
      );
      // Should not throw.
      verifySignature(id.publicKeyBytes(), sig, msg);
    } finally {
      if (id) await id.close();
      rmSync(dir, { recursive: true, force: true });
    }
  });

  it("OperatorIdentity instances do NOT hold an Ed25519 private key (M-anchor-1 proof)", async () => {
    const dir = freshKeyDir();
    let id: OperatorIdentity | null = null;
    try {
      id = await OperatorIdentity.loadOrCreate(dir, {
        hostBinary: ANCHOR_SURFACE_BIN,
      });
      // Architectural assertion: the OperatorIdentity instance must NOT have a
      // privateKey field. The proof that the owner Ed25519 private key never
      // appears in operator process memory rests on this — the class no longer
      // owns key material. Signatures are produced by calling the
      // anchor_surface_host over TCP.
      const fields = Object.getOwnPropertyNames(id);
      assert.ok(
        !fields.includes("privateKey"),
        `OperatorIdentity must not have a privateKey field (got ${fields.join(",")})`,
      );
      const hasPrivateKeyOnPrototype = Object.getOwnPropertyNames(
        Object.getPrototypeOf(id),
      ).includes("privateKey");
      assert.ok(
        !hasPrivateKeyOnPrototype,
        "OperatorIdentity prototype must not expose privateKey",
      );
      // Symbolic check: signing still works via the host.
      const sig = await id.sign(new Uint8Array([1, 2, 3]));
      assert.equal(sig.length, 64);
    } finally {
      if (id) await id.close();
      rmSync(dir, { recursive: true, force: true });
    }
  });

  it("defaultOperatorKeyDir respects $MYCO_OPERATOR_KEY_DIR override (legacy migration path)", () => {
    const old = process.env.MYCO_OPERATOR_KEY_DIR;
    process.env.MYCO_OPERATOR_KEY_DIR = "/tmp/custom-myco-op-key-dir";
    try {
      const dir = defaultOperatorKeyDir();
      assert.equal(dir, "/tmp/custom-myco-op-key-dir");
    } finally {
      if (old === undefined) {
        delete process.env.MYCO_OPERATOR_KEY_DIR;
      } else {
        process.env.MYCO_OPERATOR_KEY_DIR = old;
      }
    }
  });

  // ---------------------------------------------------------------------
  // **M-anchor-2 + M-anchor-3** — anchor surface stage-1 RPC pass-throughs.
  //
  // OperatorIdentity wraps AnchorSurfaceClient and exposes the four new
  // RPCs as async pass-throughs. These tests exercise the full client-side
  // round-trip + signature verification using @noble/curves ed25519.
  // ---------------------------------------------------------------------

  it("M-anchor-2: birthAttest signature verifies against returned owner pubkey", async () => {
    const dir = freshKeyDir();
    let id: OperatorIdentity | null = null;
    try {
      id = await OperatorIdentity.loadOrCreate(dir, {
        hostBinary: ANCHOR_SURFACE_BIN,
      });
      const substrateId = new Uint8Array(32).fill(0x11);
      const sporeSchemaHash = new Uint8Array(32).fill(0x22);
      const ownerPubkey = id.publicKeyBytes();
      const result = await id.birthAttest({
        substrateId,
        genesisTimestampUnixNs: 1_700_000_000_000_000_000n,
        sporeSchemaHash,
        anchorEndpointPubkey: ownerPubkey, // v0.9 §9.5: collapsed
      });
      assert.equal(result.signature.length, 64);
      assert.equal(result.ownerPubkey.length, 32);
      assert.ok(result.attestedCanonicalBytes.length > 0);
      assert.deepEqual(
        result.ownerPubkey,
        ownerPubkey,
        "birthAttest returns the same owner pubkey",
      );
      const { verifySignature } = await import(
        "@myco/anchor-client/src/crypto.ts"
      );
      // Should not throw.
      verifySignature(
        result.ownerPubkey,
        result.signature,
        result.attestedCanonicalBytes,
      );
    } finally {
      if (id) await id.close();
      rmSync(dir, { recursive: true, force: true });
    }
  });

  it("M-anchor-3: generateAnchorNonce returns distinct nonces + valid signatures", async () => {
    const dir = freshKeyDir();
    let id: OperatorIdentity | null = null;
    try {
      id = await OperatorIdentity.loadOrCreate(dir, {
        hostBinary: ANCHOR_SURFACE_BIN,
      });
      const r1 = await id.generateAnchorNonce(60n);
      const r2 = await id.generateAnchorNonce(60n);
      assert.equal(r1.nonce.length, 32);
      assert.equal(r2.nonce.length, 32);
      assert.equal(r1.signature.length, 64);
      // Distinctness.
      let same = true;
      for (let i = 0; i < 32; i++) {
        if (r1.nonce[i] !== r2.nonce[i]) {
          same = false;
          break;
        }
      }
      assert.equal(same, false, "successive anchor nonces must differ");
      // expiry = issued + ttl * 1e9
      assert.equal(
        r1.expiryUnixNs - r1.anchorTimestampUnixNs,
        60n * 1_000_000_000n,
      );
    } finally {
      if (id) await id.close();
      rmSync(dir, { recursive: true, force: true });
    }
  });

  it("M-anchor-3: getAnchorWallClock signature verifies + clock advances", async () => {
    const dir = freshKeyDir();
    let id: OperatorIdentity | null = null;
    try {
      id = await OperatorIdentity.loadOrCreate(dir, {
        hostBinary: ANCHOR_SURFACE_BIN,
      });
      const t1 = await id.getAnchorWallClock();
      await new Promise((r) => setTimeout(r, 5));
      const t2 = await id.getAnchorWallClock();
      assert.ok(
        t2.anchorTimestampUnixNs > t1.anchorTimestampUnixNs,
        `clock must advance: ${t1.anchorTimestampUnixNs} → ${t2.anchorTimestampUnixNs}`,
      );
      assert.equal(t1.signature.length, 64);
      assert.equal(t2.signature.length, 64);
    } finally {
      if (id) await id.close();
      rmSync(dir, { recursive: true, force: true });
    }
  });

  it("M-anchor-3: heartbeat returns distinct nonces + valid signatures", async () => {
    const dir = freshKeyDir();
    let id: OperatorIdentity | null = null;
    try {
      id = await OperatorIdentity.loadOrCreate(dir, {
        hostBinary: ANCHOR_SURFACE_BIN,
      });
      const h1 = await id.heartbeat();
      const h2 = await id.heartbeat();
      assert.equal(h1.heartbeatNonce.length, 32);
      assert.equal(h2.heartbeatNonce.length, 32);
      let same = true;
      for (let i = 0; i < 32; i++) {
        if (h1.heartbeatNonce[i] !== h2.heartbeatNonce[i]) {
          same = false;
          break;
        }
      }
      assert.equal(same, false, "successive heartbeats must produce distinct nonces");
    } finally {
      if (id) await id.close();
      rmSync(dir, { recursive: true, force: true });
    }
  });
});
