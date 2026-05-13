// Cryptographic primitives — TypeScript implementation (L1_SCHEMA §2.1 + L1_SKIN §2).
//
// MUST produce byte-identical output to:
// - kernel/shared/src/crypto.rs (Rust reference)
// - kernel/governance/src/myco_kernel_governance/crypto.py (Python)
//
// Cross-language test vectors at test_vectors/crypto_v1.json.
//
// Implementation: @noble/hashes (audited, dependency-free, pure-JS).

import { blake3 } from "@noble/hashes/blake3.js";
import { hmac } from "@noble/hashes/hmac.js";
import { sha256 } from "@noble/hashes/sha2.js";

// ---------------------------------------------------------------------------
// Error types.
// ---------------------------------------------------------------------------

/** Base crypto error (mirrors Rust `CryptoError`). */
export class CryptoError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "CryptoError";
  }
}

/** HMAC keyed by empty key (forbidden per L1_SKIN §2). */
export class HmacEmptyKey extends CryptoError {
  constructor() {
    super("HMAC key cannot be empty");
    this.name = "HmacEmptyKey";
  }
}

/** HMAC verification failed. */
export class HmacInvalid extends CryptoError {
  constructor() {
    super("HMAC verification failed");
    this.name = "HmacInvalid";
  }
}

/** Signature verification failed (M2 stub). */
export class SignatureInvalid extends CryptoError {
  constructor() {
    super("signature invalid (M2 stub — algorithm choice pending)");
    this.name = "SignatureInvalid";
  }
}

// ---------------------------------------------------------------------------
// Newtype wrappers.
// ---------------------------------------------------------------------------

/** Content-addressed Merkle hash. 32 bytes; BLAKE3-default. */
export class NodeHash {
  readonly bytes: Uint8Array;

  constructor(bytes: Uint8Array) {
    if (bytes.length !== 32) {
      throw new CryptoError(
        `NodeHash must be exactly 32 bytes; got ${bytes.length}`,
      );
    }
    this.bytes = bytes;
  }

  /** Lowercase 64-char hex representation. */
  toHex(): string {
    return bytesToHex(this.bytes);
  }

  /** Construct from a 64-char hex string. */
  static fromHex(hex: string): NodeHash {
    return new NodeHash(hexToBytes(hex));
  }

  /** Equality check by byte content. */
  equals(other: NodeHash): boolean {
    return bytesEqual(this.bytes, other.bytes);
  }
}

/** HMAC-SHA256 tag. 32 bytes. */
export class HmacTag {
  readonly bytes: Uint8Array;

  constructor(bytes: Uint8Array) {
    if (bytes.length !== 32) {
      throw new CryptoError(
        `HmacTag must be exactly 32 bytes; got ${bytes.length}`,
      );
    }
    this.bytes = bytes;
  }

  toHex(): string {
    return bytesToHex(this.bytes);
  }

  static fromHex(hex: string): HmacTag {
    return new HmacTag(hexToBytes(hex));
  }

  equals(other: HmacTag): boolean {
    return bytesEqual(this.bytes, other.bytes);
  }
}

// ---------------------------------------------------------------------------
// Primitives.
// ---------------------------------------------------------------------------

/**
 * Compute the Merkle hash of a DAG node from its parent hashes + content.
 *
 *     hash = BLAKE3(parent_count_be_u64 || parents_concat || content)
 *
 * The parent-count prefix prevents ambiguity attacks between
 * `(N parents, M-byte content)` and `(N+1 parents, (M - 32)-byte content)`
 * encodings (per L1_SCHEMA §2.1 + pass-3 mycoparasite-2 + L1_HARD_RULES C6/C7).
 */
export function merkleHash(
  parentHashes: NodeHash[],
  contentCanonicalBytes: Uint8Array,
): NodeHash {
  // Compose parent_count_be_u64 || parents... || content into a single buffer.
  const parentCountLen = 8;
  const parentsLen = parentHashes.length * 32;
  const totalLen = parentCountLen + parentsLen + contentCanonicalBytes.length;
  const buf = new Uint8Array(totalLen);

  // Write parent count as big-endian u64.
  const view = new DataView(buf.buffer, buf.byteOffset, parentCountLen);
  // BigUint64 is BE-with-second-arg-false; we want BE so pass false.
  view.setBigUint64(0, BigInt(parentHashes.length), false);

  // Concat parent bytes.
  let offset = parentCountLen;
  for (const ph of parentHashes) {
    buf.set(ph.bytes, offset);
    offset += 32;
  }

  // Append content.
  buf.set(contentCanonicalBytes, offset);

  // BLAKE3.
  const digest = blake3(buf);
  return new NodeHash(digest);
}

/**
 * Compute HMAC-SHA256 over `canonicalBytes` keyed by `key`.
 *
 * Per L1_SKIN §2: `envelope_digest = HMAC(operator_token,
 * canonical_envelope_fields || payload)`. Empty key forbidden.
 *
 * @throws {HmacEmptyKey} if `key` is empty.
 */
export function hmacSign(key: Uint8Array, canonicalBytes: Uint8Array): HmacTag {
  if (key.length === 0) {
    throw new HmacEmptyKey();
  }
  const tag = hmac(sha256, key, canonicalBytes);
  return new HmacTag(tag);
}

/**
 * Verify an HMAC-SHA256 tag matches the canonical bytes under the given key.
 *
 * Constant-time comparison.
 *
 * @throws {HmacEmptyKey} if `key` is empty.
 * @throws {HmacInvalid} if the recomputed tag does not match `tag`.
 */
export function hmacVerify(
  key: Uint8Array,
  canonicalBytes: Uint8Array,
  tag: HmacTag,
): void {
  if (key.length === 0) {
    throw new HmacEmptyKey();
  }
  const expected = hmacSign(key, canonicalBytes);
  if (!constantTimeEqual(expected.bytes, tag.bytes)) {
    throw new HmacInvalid();
  }
}

/**
 * Verify a signature (M2 stub — actual algorithm M2-decided).
 *
 * L1_GOVERNANCE §7 lists Ed25519, ECDSA-P256, post-quantum candidates as L4
 * options. M2 stub throws; M3+ lands production path.
 */
export function verifySignature(
  _publicKey: Uint8Array,
  _signature: Uint8Array,
  _canonicalBytes: Uint8Array,
): void {
  throw new SignatureInvalid();
}

// ---------------------------------------------------------------------------
// Internal byte helpers.
// ---------------------------------------------------------------------------

function bytesToHex(bytes: Uint8Array): string {
  let s = "";
  for (const b of bytes) {
    s += b.toString(16).padStart(2, "0");
  }
  return s;
}

function hexToBytes(hex: string): Uint8Array {
  if (hex.length % 2 !== 0) {
    throw new CryptoError(`odd hex length: ${hex.length}`);
  }
  const out = new Uint8Array(hex.length / 2);
  for (let i = 0; i < out.length; i++) {
    out[i] = parseInt(hex.substring(i * 2, i * 2 + 2), 16);
  }
  return out;
}

function bytesEqual(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) {
    if (a[i] !== b[i]) return false;
  }
  return true;
}

/** Constant-time byte comparison (defense against timing oracles). */
function constantTimeEqual(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) {
    diff |= a[i]! ^ b[i]!;
  }
  return diff === 0;
}
