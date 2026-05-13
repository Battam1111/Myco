// Canonical-bytes serializer — TypeScript implementation (L1_SCHEMA §3.1 + L0 §9.3).
//
// MUST produce byte-identical output to:
// - kernel/shared/src/canonical_bytes.rs (Rust reference)
// - kernel/governance/src/myco_kernel_governance/canonical_bytes.py (Python)
//
// Cross-language test vectors at test_vectors/canonical_bytes_v1.json.
//
// Drift from spec = L1_HARD_RULES C18 canonical_bytes_render_drift (CRITICAL).

/**
 * Typed value tree — the input domain for the canonical-bytes serializer.
 *
 * Discriminated union; each variant carries its specific payload.
 * Matches Rust's `Value` enum in `kernel/shared::canonical_bytes`.
 */
export type Value =
  | { type: "null" }
  | { type: "bool"; value: boolean }
  | { type: "int"; value: bigint } // i64 two's-complement
  | { type: "uint"; value: bigint } // u64
  | { type: "string"; value: string } // UTF-8
  | { type: "bytes"; value: Uint8Array }
  | { type: "array"; value: Value[] }
  | { type: "map"; value: Map<string, Value> }
  | { type: "timestamp"; value: bigint } // i64 unix nanoseconds
  | { type: "hash"; value: Uint8Array }; // 32 bytes

/**
 * Canonical bytes — newtype wrapping `Uint8Array` to prevent accidental mixing
 * with arbitrary byte sequences in the type system.
 */
export class CanonicalBytes {
  readonly bytes: Uint8Array;

  constructor(bytes: Uint8Array) {
    this.bytes = bytes;
  }

  /** Hex representation (lowercase, no separator). */
  toHex(): string {
    return Array.from(this.bytes)
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
  }

  /** Length in bytes. */
  get length(): number {
    return this.bytes.length;
  }
}

/** Canonical-bytes serialization error. */
export class CanonicalBytesError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "CanonicalBytesError";
  }
}

/** Type tag bytes (must match Rust + Python). */
export const TAG = {
  NULL: 0x00,
  BOOL: 0x01,
  INT: 0x10,
  UINT: 0x11,
  STRING: 0x20,
  BYTES: 0x21,
  ARRAY: 0x30,
  MAP: 0x31,
  TIMESTAMP: 0x40,
  HASH: 0x41,
} as const;

/**
 * Write a varint (7 bits per byte; MSB=1 if more bytes follow; MSB=0 on last).
 *
 * Identical to the Rust `write_varint` and Python `write_varint`.
 *
 * Accepts both `number` and `bigint`; bigint is preferred for u64-range
 * inputs (counts of arrays/maps fit in usize on all reasonable platforms,
 * but bigint avoids ambiguity).
 */
export function writeVarint(n: number | bigint, buf: number[]): void {
  let nb = typeof n === "bigint" ? n : BigInt(n);
  if (nb < 0n) {
    throw new CanonicalBytesError(`varint cannot encode negative: ${nb}`);
  }
  while (nb >= 0x80n) {
    buf.push(Number((nb & 0x7fn) | 0x80n));
    nb >>= 7n;
  }
  buf.push(Number(nb));
}

/**
 * Write an i64 (signed, two's-complement) as 8 bytes big-endian.
 */
function writeI64BE(n: bigint, buf: number[]): void {
  // Clamp to i64 range; throw if out-of-range.
  const MAX = (1n << 63n) - 1n;
  const MIN = -(1n << 63n);
  if (n < MIN || n > MAX) {
    throw new CanonicalBytesError(`i64 out of range: ${n}`);
  }
  // Convert negative to two's-complement.
  let v = n < 0n ? (1n << 64n) + n : n;
  for (let i = 7; i >= 0; i--) {
    buf.push(Number((v >> BigInt(i * 8)) & 0xffn));
  }
}

/**
 * Write a u64 (unsigned) as 8 bytes big-endian.
 */
function writeU64BE(n: bigint, buf: number[]): void {
  const MAX = (1n << 64n) - 1n;
  if (n < 0n || n > MAX) {
    throw new CanonicalBytesError(`u64 out of range: ${n}`);
  }
  for (let i = 7; i >= 0; i--) {
    buf.push(Number((n >> BigInt(i * 8)) & 0xffn));
  }
}

/**
 * UTF-8 encode a string.
 */
function utf8Encode(s: string): Uint8Array {
  return new TextEncoder().encode(s);
}

/**
 * Encode a [`Value`] to canonical bytes.
 *
 * Deterministic: same input → byte-identical output across all language
 * implementations. Matches:
 * - kernel/shared::canonical_bytes::encode (Rust)
 * - myco_kernel_governance.canonical_bytes.encode (Python)
 */
export function encode(value: Value): CanonicalBytes {
  const buf: number[] = [];
  encodeInto(value, buf);
  return new CanonicalBytes(new Uint8Array(buf));
}

function encodeInto(value: Value, buf: number[]): void {
  switch (value.type) {
    case "null":
      buf.push(TAG.NULL);
      break;

    case "bool":
      buf.push(TAG.BOOL);
      buf.push(value.value ? 0x01 : 0x00);
      break;

    case "int":
      buf.push(TAG.INT);
      writeI64BE(value.value, buf);
      break;

    case "uint":
      buf.push(TAG.UINT);
      writeU64BE(value.value, buf);
      break;

    case "string": {
      buf.push(TAG.STRING);
      const utf8 = utf8Encode(value.value);
      writeVarint(utf8.length, buf);
      for (const b of utf8) buf.push(b);
      break;
    }

    case "bytes": {
      buf.push(TAG.BYTES);
      writeVarint(value.value.length, buf);
      for (const b of value.value) buf.push(b);
      break;
    }

    case "array":
      buf.push(TAG.ARRAY);
      writeVarint(value.value.length, buf);
      for (const item of value.value) encodeInto(item, buf);
      break;

    case "map": {
      buf.push(TAG.MAP);
      writeVarint(value.value.size, buf);
      // Sort entries by canonical-bytes of key (key is a String value).
      const keyed: { keyCanonical: Uint8Array; value: Value }[] = [];
      for (const [k, v] of value.value) {
        const keyCb = encode({ type: "string", value: k });
        keyed.push({ keyCanonical: keyCb.bytes, value: v });
      }
      keyed.sort((a, b) => compareBytes(a.keyCanonical, b.keyCanonical));
      for (const entry of keyed) {
        for (const b of entry.keyCanonical) buf.push(b);
        encodeInto(entry.value, buf);
      }
      break;
    }

    case "timestamp":
      buf.push(TAG.TIMESTAMP);
      writeI64BE(value.value, buf);
      break;

    case "hash":
      if (value.value.length !== 32) {
        throw new CanonicalBytesError(
          `hash must be exactly 32 bytes; got ${value.value.length}`,
        );
      }
      buf.push(TAG.HASH);
      for (const b of value.value) buf.push(b);
      break;
  }
}

/**
 * Lexicographic byte comparison. Returns negative / 0 / positive in
 * standard Array.prototype.sort convention.
 */
function compareBytes(a: Uint8Array, b: Uint8Array): number {
  const min = Math.min(a.length, b.length);
  for (let i = 0; i < min; i++) {
    const diff = a[i]! - b[i]!;
    if (diff !== 0) return diff;
  }
  return a.length - b.length;
}
