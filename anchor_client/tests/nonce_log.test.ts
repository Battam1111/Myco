// Tests for nonce_log.ts.

import { test } from "node:test";
import { strict as assert } from "node:assert";

import { NodeHash } from "../src/crypto.ts";
import {
  DEFAULT_NONCE_TTL_SECONDS,
  FixedClockSource,
  FixedRandomSource,
  NonceAlreadyConsumed,
  NonceBindingMismatch,
  NonceExpired,
  NonceLog,
  NONCE_LENGTH,
  RateLimitExceeded,
  UnknownNonce,
} from "../src/nonce_log.ts";

function makeHash(byte: number): NodeHash {
  return new NodeHash(new Uint8Array(32).fill(byte));
}

function makeLog(opts?: {
  ttl?: number;
  rateLimit?: number;
  startTime?: number;
}): { log: NonceLog; clock: FixedClockSource } {
  const clock = new FixedClockSource(opts?.startTime ?? 1_000_000);
  const random = new FixedRandomSource();
  const log = new NonceLog(
    random,
    clock,
    opts?.ttl ?? DEFAULT_NONCE_TTL_SECONDS,
    opts?.rateLimit ?? 60,
  );
  return { log, clock };
}

// ---------------------------------------------------------------------------
// Issue → consume happy path.
// ---------------------------------------------------------------------------

test("issue nonce returns 32 bytes", () => {
  const { log } = makeLog();
  const nonce = log.issueNonce("sub_001", makeHash(0xaa), makeHash(0xbb));
  assert.equal(nonce.length, NONCE_LENGTH);
});

test("issue → consume round-trip", () => {
  const { log } = makeLog();
  const mh = makeHash(0xaa);
  const dt = makeHash(0xbb);
  const nonce = log.issueNonce("sub_001", mh, dt);
  log.consume(nonce, mh, dt); // should not throw
  assert.ok(log.isConsumed(nonce));
});

test("issue increments issued count", () => {
  const { log } = makeLog();
  assert.equal(log.issuedCount(), 0);
  log.issueNonce("sub_001", makeHash(0xaa), makeHash(0xbb));
  assert.equal(log.issuedCount(), 1);
  log.issueNonce("sub_001", makeHash(0xaa), makeHash(0xbb));
  assert.equal(log.issuedCount(), 2);
});

test("consume moves nonce from issued to consumed", () => {
  const { log } = makeLog();
  const mh = makeHash(0xaa);
  const dt = makeHash(0xbb);
  const nonce = log.issueNonce("sub_001", mh, dt);
  assert.equal(log.issuedCount(), 1);
  assert.equal(log.consumedCount(), 0);
  log.consume(nonce, mh, dt);
  assert.equal(log.issuedCount(), 0);
  assert.equal(log.consumedCount(), 1);
});

// ---------------------------------------------------------------------------
// Replay protection.
// ---------------------------------------------------------------------------

test("consume twice rejected (NonceAlreadyConsumed)", () => {
  const { log } = makeLog();
  const mh = makeHash(0xaa);
  const dt = makeHash(0xbb);
  const nonce = log.issueNonce("sub_001", mh, dt);
  log.consume(nonce, mh, dt);
  assert.throws(() => log.consume(nonce, mh, dt), NonceAlreadyConsumed);
});

test("unknown nonce rejected (UnknownNonce)", () => {
  const { log } = makeLog();
  const fakeNonce = new Uint8Array(32).fill(0xff);
  assert.throws(
    () => log.consume(fakeNonce, makeHash(0xaa), makeHash(0xbb)),
    UnknownNonce,
  );
});

// ---------------------------------------------------------------------------
// Binding mismatch (pass-3 mycoparasite-5 closure).
// ---------------------------------------------------------------------------

test("mutation_hash mismatch rejected", () => {
  const { log } = makeLog();
  const original_mh = makeHash(0xaa);
  const dt = makeHash(0xbb);
  const nonce = log.issueNonce("sub_001", original_mh, dt);
  // Substrate tries to use the nonce with a DIFFERENT mutation_hash.
  assert.throws(
    () => log.consume(nonce, makeHash(0x99), dt),
    NonceBindingMismatch,
  );
});

test("dag_tip_hash mismatch rejected", () => {
  const { log } = makeLog();
  const mh = makeHash(0xaa);
  const original_dt = makeHash(0xbb);
  const nonce = log.issueNonce("sub_001", mh, original_dt);
  assert.throws(
    () => log.consume(nonce, mh, makeHash(0xcc)),
    NonceBindingMismatch,
  );
});

// ---------------------------------------------------------------------------
// TTL expiry.
// ---------------------------------------------------------------------------

test("nonce expires after TTL", () => {
  const { log, clock } = makeLog({ ttl: 60 });
  const mh = makeHash(0xaa);
  const dt = makeHash(0xbb);
  const nonce = log.issueNonce("sub_001", mh, dt);
  clock.advance(61); // exceed TTL
  assert.throws(() => log.consume(nonce, mh, dt), NonceExpired);
});

test("nonce valid at TTL boundary", () => {
  const { log, clock } = makeLog({ ttl: 60 });
  const mh = makeHash(0xaa);
  const dt = makeHash(0xbb);
  const nonce = log.issueNonce("sub_001", mh, dt);
  clock.advance(60); // exactly at TTL — still valid (>, not >=)
  log.consume(nonce, mh, dt); // should not throw
});

test("purgeExpired removes expired issuances", () => {
  const { log, clock } = makeLog({ ttl: 60 });
  log.issueNonce("sub_001", makeHash(0xaa), makeHash(0xbb));
  log.issueNonce("sub_001", makeHash(0xaa), makeHash(0xbb));
  log.issueNonce("sub_001", makeHash(0xaa), makeHash(0xbb));
  assert.equal(log.issuedCount(), 3);
  clock.advance(61);
  const purged = log.purgeExpired();
  assert.equal(purged, 3);
  assert.equal(log.issuedCount(), 0);
});

// ---------------------------------------------------------------------------
// Rate limit (L1_GOVERNANCE §2.2: attestation_request_saturation).
// ---------------------------------------------------------------------------

test("rate limit triggers after threshold", () => {
  const { log } = makeLog({ rateLimit: 5 });
  for (let i = 0; i < 5; i++) {
    log.issueNonce("sub_001", makeHash(0xaa), makeHash(0xbb));
  }
  assert.throws(
    () => log.issueNonce("sub_001", makeHash(0xaa), makeHash(0xbb)),
    RateLimitExceeded,
  );
});

test("rate limit per substrate (sub_002 not affected by sub_001's hits)", () => {
  const { log } = makeLog({ rateLimit: 3 });
  for (let i = 0; i < 3; i++) {
    log.issueNonce("sub_001", makeHash(0xaa), makeHash(0xbb));
  }
  // sub_002 can still issue.
  log.issueNonce("sub_002", makeHash(0xaa), makeHash(0xbb));
});

test("rate limit window slides", () => {
  const { log, clock } = makeLog({ rateLimit: 3 });
  for (let i = 0; i < 3; i++) {
    log.issueNonce("sub_001", makeHash(0xaa), makeHash(0xbb));
  }
  clock.advance(61); // past 60-second window
  // sub_001 can issue again.
  log.issueNonce("sub_001", makeHash(0xaa), makeHash(0xbb));
});

// ---------------------------------------------------------------------------
// isConsumed query.
// ---------------------------------------------------------------------------

test("isConsumed reports consumption", () => {
  const { log } = makeLog();
  const mh = makeHash(0xaa);
  const dt = makeHash(0xbb);
  const nonce = log.issueNonce("sub_001", mh, dt);
  assert.equal(log.isConsumed(nonce), false);
  log.consume(nonce, mh, dt);
  assert.equal(log.isConsumed(nonce), true);
});

test("isConsumed false for never-issued nonce", () => {
  const { log } = makeLog();
  const fake = new Uint8Array(32).fill(0xff);
  assert.equal(log.isConsumed(fake), false);
});

// ---------------------------------------------------------------------------
// Random source: each issued nonce is unique (deterministic FixedRandomSource).
// ---------------------------------------------------------------------------

test("each nonce is unique", () => {
  const { log } = makeLog();
  const seen = new Set<string>();
  for (let i = 0; i < 10; i++) {
    const nonce = log.issueNonce("sub_001", makeHash(0xaa), makeHash(0xbb));
    const key = Array.from(nonce, (b) => b.toString(16).padStart(2, "0")).join("");
    assert.ok(!seen.has(key));
    seen.add(key);
  }
});
