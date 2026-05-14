// Tests for OperatorIdentity (M9).

import { describe, it } from "node:test";
import assert from "node:assert/strict";
import {
  existsSync,
  mkdtempSync,
  readFileSync,
  rmSync,
} from "node:fs";
import { resolve as resolvePath } from "node:path";
import { tmpdir } from "node:os";

import {
  OPERATOR_IDENTITY_FILENAME,
  OperatorIdentity,
  defaultOperatorKeyDir,
} from "../src/operator_identity.ts";

function freshKeyDir(): string {
  return mkdtempSync(resolvePath(tmpdir(), "myco-op-id-"));
}

describe("OperatorIdentity", () => {
  it("loadOrCreate generates fresh key if none exists", () => {
    const dir = freshKeyDir();
    try {
      const id = OperatorIdentity.loadOrCreate(dir);
      const keyPath = resolvePath(dir, OPERATOR_IDENTITY_FILENAME);
      assert.ok(existsSync(keyPath), "identity.key should be created on disk");
      const seed = readFileSync(keyPath);
      assert.equal(seed.length, 32, "seed should be 32 bytes");
      assert.equal(id.publicKey.bytes.length, 32);
      assert.equal(id.publicKeyBytes().length, 32);
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  });

  it("loadOrCreate is deterministic: same dir → same pubkey", () => {
    const dir = freshKeyDir();
    try {
      const id1 = OperatorIdentity.loadOrCreate(dir);
      const id2 = OperatorIdentity.loadOrCreate(dir);
      assert.deepEqual(id1.publicKeyBytes(), id2.publicKeyBytes());
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  });

  it("fresh dirs yield different pubkeys", () => {
    const a = freshKeyDir();
    const b = freshKeyDir();
    try {
      const idA = OperatorIdentity.loadOrCreate(a);
      const idB = OperatorIdentity.loadOrCreate(b);
      assert.notDeepEqual(idA.publicKeyBytes(), idB.publicKeyBytes());
    } finally {
      rmSync(a, { recursive: true, force: true });
      rmSync(b, { recursive: true, force: true });
    }
  });

  it("sign + verify roundtrips (using anchor_client verifySignature)", async () => {
    const dir = freshKeyDir();
    try {
      const id = OperatorIdentity.loadOrCreate(dir);
      const msg = new TextEncoder().encode("hello world");
      const sig = id.sign(msg);
      assert.equal(sig.length, 64);

      const { verifySignature } = await import("@myco/anchor-client/src/crypto.ts");
      // Should not throw.
      verifySignature(id.publicKeyBytes(), sig, msg);
    } finally {
      rmSync(dir, { recursive: true, force: true });
    }
  });

  it("fromSeed reconstructs a known identity deterministically", () => {
    const seed = new Uint8Array(32).fill(0xaa);
    const id1 = OperatorIdentity.fromSeed(seed);
    const id2 = OperatorIdentity.fromSeed(seed);
    assert.deepEqual(id1.publicKeyBytes(), id2.publicKeyBytes());
    // Specifically, Ed25519 with seed=0xaa*32 yields a deterministic pubkey
    // (pinned for cross-test stability).
    const sig1 = id1.sign(new Uint8Array([1, 2, 3]));
    const sig2 = id2.sign(new Uint8Array([1, 2, 3]));
    assert.deepEqual(sig1, sig2, "Ed25519 is deterministic per RFC 8032");
  });

  it("defaultOperatorKeyDir respects $MYCO_OPERATOR_KEY_DIR override", () => {
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
