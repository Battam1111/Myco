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

  it("sign + verify roundtrips (using anchor_client verifySignature)", async () => {
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
});
