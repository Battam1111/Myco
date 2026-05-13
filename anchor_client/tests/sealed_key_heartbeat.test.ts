// Tests for sealed_key.ts + heartbeat.ts.

import { test } from "node:test";
import { strict as assert } from "node:assert";

import { Ed25519PrivateKey } from "../src/crypto.ts";
import { InMemorySealedKey } from "../src/sealed_key.ts";
import {
  HeartbeatInvalid,
  heartbeatCanonicalBytes,
  heartbeatStalenessSeconds,
  signHeartbeat,
  verifyHeartbeat,
} from "../src/heartbeat.ts";

// ---------------------------------------------------------------------------
// InMemorySealedKey
// ---------------------------------------------------------------------------

test("InMemorySealedKey: pubkey + sign round-trip", () => {
  const seed = new Uint8Array(32).fill(0x42);
  const sealed = InMemorySealedKey.fromSeed(seed);
  const pub = sealed.publicKey();
  const msg = new TextEncoder().encode("hello");
  const sig = sealed.sign(msg);
  // The signature should verify with the corresponding pubkey.
  const expected_priv = Ed25519PrivateKey.fromSeed(seed);
  const expected_sig = expected_priv.sign(msg);
  assert.equal(sig.toHex(), expected_sig.toHex());
});

test("InMemorySealedKey: toString redacts", () => {
  const sealed = InMemorySealedKey.fromSeed(new Uint8Array(32).fill(0xff));
  assert.ok(sealed.toString().includes("NOT PRODUCTION-SAFE"));
  assert.ok(!sealed.toString().includes("ff"));
});

test("InMemorySealedKey: JSON.stringify redacts", () => {
  const sealed = InMemorySealedKey.fromSeed(new Uint8Array(32).fill(0xff));
  const s = JSON.stringify(sealed);
  assert.ok(s.includes("NOT PRODUCTION-SAFE"));
  assert.ok(!s.includes("ff"));
});

test("InMemorySealedKey: same seed → same pubkey", () => {
  const seed = new Uint8Array(32).fill(0x01);
  const a = InMemorySealedKey.fromSeed(seed);
  const b = InMemorySealedKey.fromSeed(seed);
  assert.equal(a.publicKey().toHex(), b.publicKey().toHex());
});

// ---------------------------------------------------------------------------
// Heartbeat canonical bytes
// ---------------------------------------------------------------------------

test("heartbeatCanonicalBytes: deterministic", () => {
  const a = heartbeatCanonicalBytes("sub_001", 1_700_000_000);
  const b = heartbeatCanonicalBytes("sub_001", 1_700_000_000);
  assert.equal(a.toHex(), b.toHex());
});

test("heartbeatCanonicalBytes: differs by substrate_id", () => {
  const a = heartbeatCanonicalBytes("sub_001", 1_700_000_000);
  const b = heartbeatCanonicalBytes("sub_002", 1_700_000_000);
  assert.notEqual(a.toHex(), b.toHex());
});

test("heartbeatCanonicalBytes: differs by timestamp", () => {
  const a = heartbeatCanonicalBytes("sub_001", 1_700_000_000);
  const b = heartbeatCanonicalBytes("sub_001", 1_700_000_001);
  assert.notEqual(a.toHex(), b.toHex());
});

// ---------------------------------------------------------------------------
// Sign + verify round-trip
// ---------------------------------------------------------------------------

test("signHeartbeat + verifyHeartbeat: round-trip", () => {
  const sealed = InMemorySealedKey.fromSeed(new Uint8Array(32).fill(0x01));
  const event = signHeartbeat(sealed, "sub_001", 1_700_000_000);
  verifyHeartbeat(event, sealed.publicKey()); // should not throw
});

test("verifyHeartbeat: wrong owner key rejected", () => {
  const owner_a = InMemorySealedKey.fromSeed(new Uint8Array(32).fill(0x01));
  const owner_b = InMemorySealedKey.fromSeed(new Uint8Array(32).fill(0x02));
  const event = signHeartbeat(owner_a, "sub_001", 1_700_000_000);
  // Verify against the WRONG owner's pubkey.
  assert.throws(
    () => verifyHeartbeat(event, owner_b.publicKey()),
    HeartbeatInvalid,
  );
});

test("verifyHeartbeat: tampered timestamp rejected", () => {
  const sealed = InMemorySealedKey.fromSeed(new Uint8Array(32).fill(0x01));
  const event = signHeartbeat(sealed, "sub_001", 1_700_000_000);
  // Mutate the timestamp post-signing.
  const tampered = { ...event, anchorTimestampUnixSeconds: 1_700_000_001 };
  assert.throws(
    () => verifyHeartbeat(tampered, sealed.publicKey()),
    HeartbeatInvalid,
  );
});

test("verifyHeartbeat: tampered substrate_id rejected", () => {
  const sealed = InMemorySealedKey.fromSeed(new Uint8Array(32).fill(0x01));
  const event = signHeartbeat(sealed, "sub_001", 1_700_000_000);
  const tampered = { ...event, substrateId: "sub_002" };
  assert.throws(
    () => verifyHeartbeat(tampered, sealed.publicKey()),
    HeartbeatInvalid,
  );
});

// ---------------------------------------------------------------------------
// Staleness calculation
// ---------------------------------------------------------------------------

test("heartbeatStalenessSeconds: positive elapsed", () => {
  const event = {
    substrateId: "sub_001",
    anchorTimestampUnixSeconds: 1_700_000_000,
    ownerSignature: { bytes: new Uint8Array(64), toHex: () => "" } as never,
  };
  assert.equal(heartbeatStalenessSeconds(event, 1_700_000_300), 300);
});

test("heartbeatStalenessSeconds: zero on simultaneous", () => {
  const event = {
    substrateId: "sub_001",
    anchorTimestampUnixSeconds: 1_700_000_000,
    ownerSignature: { bytes: new Uint8Array(64), toHex: () => "" } as never,
  };
  assert.equal(heartbeatStalenessSeconds(event, 1_700_000_000), 0);
});

test("heartbeatStalenessSeconds: negative on clock skew", () => {
  const event = {
    substrateId: "sub_001",
    anchorTimestampUnixSeconds: 1_700_000_300,
    ownerSignature: { bytes: new Uint8Array(64), toHex: () => "" } as never,
  };
  // Current time is 300s BEFORE the heartbeat (future heartbeat).
  assert.equal(heartbeatStalenessSeconds(event, 1_700_000_000), -300);
});
