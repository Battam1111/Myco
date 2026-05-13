// Cross-language crypto parity tests.
//
// Loads `test_vectors/crypto_v1.json` and verifies that the TypeScript
// merkle_hash and hmac_sign implementations produce byte-identical output
// to every vector in the JSON. Same JSON is consumed by Rust + Python.

import { test } from "node:test";
import { strict as assert } from "node:assert";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import {
  hmacSign,
  hmacVerify,
  HmacEmptyKey,
  HmacInvalid,
  HmacTag,
  merkleHash,
  NodeHash,
  SignatureInvalid,
  CryptoError,
  verifySignature,
} from "../src/crypto.ts";

const __dirname = dirname(fileURLToPath(import.meta.url));
const vectorsPath = join(__dirname, "..", "..", "test_vectors", "crypto_v1.json");
const vectorsRaw = readFileSync(vectorsPath, "utf-8");
const vectors = JSON.parse(vectorsRaw) as CryptoVectorsFile;

interface CryptoVectorsFile {
  merkle_hash: { vectors: MerkleCase[] };
  hmac_sha256: { vectors: HmacCase[] };
  empty_key_must_error: { test_cases: EmptyKeyCase[] };
}

interface MerkleCase {
  name: string;
  parents_hex: string[];
  content_hex: string;
  output_hex: string;
}

interface HmacCase {
  name: string;
  key_hex: string;
  msg_hex: string;
  output_hex: string;
}

interface EmptyKeyCase {
  key_hex: string;
  msg_hex: string;
}

function hexToBytes(hex: string): Uint8Array {
  if (hex.length % 2 !== 0) throw new Error(`odd hex length: ${hex.length}`);
  const out = new Uint8Array(hex.length / 2);
  for (let i = 0; i < out.length; i++) {
    out[i] = parseInt(hex.substring(i * 2, i * 2 + 2), 16);
  }
  return out;
}

// ---------- Merkle hash vectors ----------
for (const v of vectors.merkle_hash.vectors) {
  test(`merkle_hash: ${v.name}`, () => {
    const parents = v.parents_hex.map((h) => new NodeHash(hexToBytes(h)));
    const content = hexToBytes(v.content_hex);
    const got = merkleHash(parents, content);
    assert.equal(
      got.toHex(),
      v.output_hex,
      `merkle vector "${v.name}" mismatch:\n  expected: ${v.output_hex}\n  got:      ${got.toHex()}`,
    );
  });
}

// ---------- HMAC vectors ----------
for (const v of vectors.hmac_sha256.vectors) {
  test(`hmac_sha256: ${v.name}`, () => {
    const key = hexToBytes(v.key_hex);
    const msg = hexToBytes(v.msg_hex);
    const got = hmacSign(key, msg);
    assert.equal(
      got.toHex(),
      v.output_hex,
      `hmac vector "${v.name}" mismatch:\n  expected: ${v.output_hex}\n  got:      ${got.toHex()}`,
    );
  });
}

// ---------- Empty key must error ----------
for (const c of vectors.empty_key_must_error.test_cases) {
  test(`empty_key_rejected: msg_hex=${c.msg_hex}`, () => {
    const key = hexToBytes(c.key_hex);
    const msg = hexToBytes(c.msg_hex);
    assert.throws(() => hmacSign(key, msg), HmacEmptyKey);
  });
}

// ---------- Property + error tests ----------
test("merkle_hash determinism", () => {
  const parent = new NodeHash(new Uint8Array(32).fill(0x01));
  const content = new TextEncoder().encode("hello");
  assert.equal(
    merkleHash([parent], content).toHex(),
    merkleHash([parent], content).toHex(),
  );
});

test("merkle_hash different parents → different hash", () => {
  const p1 = new NodeHash(new Uint8Array(32).fill(0x01));
  const p2 = new NodeHash(new Uint8Array(32).fill(0x02));
  const content = new TextEncoder().encode("hello");
  const h1 = merkleHash([p1], content).toHex();
  const h2 = merkleHash([p2], content).toHex();
  assert.notEqual(h1, h2);
});

test("merkle_hash parent_count disambiguation (mycoparasite-2)", () => {
  // Without the parent_count prefix, these two would produce identical BLAKE3 input.
  const p = new NodeHash(new Uint8Array(32).fill(0xab));
  const content32 = new Uint8Array(32).fill(0xcd);
  const p2 = new NodeHash(new Uint8Array(32).fill(0xcd));

  const h1 = merkleHash([p], content32);
  const h2 = merkleHash([p, p2], new Uint8Array(0));
  assert.notEqual(h1.toHex(), h2.toHex());
});

test("hmac round-trip", () => {
  const key = new TextEncoder().encode("operator_token_test");
  const msg = new TextEncoder().encode("canonical_envelope_bytes");
  const tag = hmacSign(key, msg);
  hmacVerify(key, msg, tag); // should not throw
});

test("hmac wrong key fails verify", () => {
  const msg = new TextEncoder().encode("hello");
  const tag = hmacSign(new TextEncoder().encode("correct_key"), msg);
  assert.throws(
    () => hmacVerify(new TextEncoder().encode("wrong_key"), msg, tag),
    HmacInvalid,
  );
});

test("hmac tampered msg fails verify", () => {
  const key = new TextEncoder().encode("test_key");
  const tag = hmacSign(key, new TextEncoder().encode("original"));
  assert.throws(
    () => hmacVerify(key, new TextEncoder().encode("tampered"), tag),
    HmacInvalid,
  );
});

test("hmac_verify empty key rejected", () => {
  const fakeTag = new HmacTag(new Uint8Array(32));
  assert.throws(
    () =>
      hmacVerify(new Uint8Array(0), new TextEncoder().encode("msg"), fakeTag),
    HmacEmptyKey,
  );
});

test("NodeHash wrong length rejected", () => {
  assert.throws(() => new NodeHash(new Uint8Array(16)), CryptoError);
});

test("HmacTag wrong length rejected", () => {
  assert.throws(() => new HmacTag(new Uint8Array(16)), CryptoError);
});

test("verify_signature is M2 stub", () => {
  assert.throws(
    () =>
      verifySignature(
        new TextEncoder().encode("pubkey"),
        new TextEncoder().encode("sig"),
        new TextEncoder().encode("content"),
      ),
    SignatureInvalid,
  );
});

test("NodeHash equality", () => {
  const a = new NodeHash(new Uint8Array(32).fill(0xff));
  const b = new NodeHash(new Uint8Array(32).fill(0xff));
  const c = new NodeHash(new Uint8Array(32).fill(0x00));
  assert.ok(a.equals(b));
  assert.ok(!a.equals(c));
});

test("NodeHash hex round-trip", () => {
  const hex = "abababababababababababababababababababababababababababababababab";
  const h = NodeHash.fromHex(hex);
  assert.equal(h.toHex(), hex);
});
