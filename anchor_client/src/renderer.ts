// Canonical-bytes rendering — TypeScript implementation (L0 §9.3 + L1_GOVERNANCE §2.4).
//
// Per L0 §9.3 canonical-bytes doctrine: substrate emits canonical bytes;
// substrate does NOT narrate. The anchor-surface client renders
// deterministically for owner review.
//
// This module:
//
// - Decodes canonical-bytes (TLV format) back into the typed Value tree.
// - Renders Value trees as human-readable strings for owner review.
// - The decode is byte-deterministic: identical canonical bytes → identical
//   Value tree. The render is line-deterministic: identical Value tree →
//   identical text output. Together: identical canonical bytes → identical
//   rendered text, regardless of which anchor_client instance is used (per
//   L1_HARD_RULES C18 canonical_bytes_render_drift detection).
//
// ## Render format
//
// The render uses an indented S-expression-like format that's both compact
// and human-readable. The format is committed at L1 (so two anchor_client
// instances agree) but DOES NOT change the underlying canonical-bytes spec
// (only the display layer).

import {
  CanonicalBytes,
  CanonicalBytesError,
  TAG,
  type Value,
} from "./canonical_bytes.ts";

// ---------------------------------------------------------------------------
// Decoder: canonical-bytes → Value.
// ---------------------------------------------------------------------------

/** Error thrown on malformed canonical bytes. */
export class CanonicalBytesDecodeError extends CanonicalBytesError {
  constructor(message: string) {
    super(`canonical-bytes decode error: ${message}`);
    this.name = "CanonicalBytesDecodeError";
  }
}

interface Reader {
  bytes: Uint8Array;
  offset: number;
}

function readByte(r: Reader): number {
  if (r.offset >= r.bytes.length) {
    throw new CanonicalBytesDecodeError(
      `unexpected end of input at offset ${r.offset}`,
    );
  }
  return r.bytes[r.offset++]!;
}

function readBytes(r: Reader, n: number): Uint8Array {
  if (r.offset + n > r.bytes.length) {
    throw new CanonicalBytesDecodeError(
      `unexpected end of input: needed ${n} bytes at offset ${r.offset}, have ${r.bytes.length - r.offset}`,
    );
  }
  const slice = r.bytes.slice(r.offset, r.offset + n);
  r.offset += n;
  return slice;
}

function readVarint(r: Reader): bigint {
  let result = 0n;
  let shift = 0n;
  // Bound the loop to avoid pathological inputs (a u64 fits in ≤10 varint bytes).
  for (let i = 0; i < 10; i++) {
    const b = readByte(r);
    result |= BigInt(b & 0x7f) << shift;
    if ((b & 0x80) === 0) {
      return result;
    }
    shift += 7n;
  }
  throw new CanonicalBytesDecodeError("varint too long (>10 bytes)");
}

function readI64BE(r: Reader): bigint {
  const slice = readBytes(r, 8);
  let v = 0n;
  for (const b of slice) {
    v = (v << 8n) | BigInt(b);
  }
  // Sign-extend if high bit set.
  if (v >= 1n << 63n) {
    v -= 1n << 64n;
  }
  return v;
}

function readU64BE(r: Reader): bigint {
  const slice = readBytes(r, 8);
  let v = 0n;
  for (const b of slice) {
    v = (v << 8n) | BigInt(b);
  }
  return v;
}

function decodeOne(r: Reader): Value {
  const tag = readByte(r);
  switch (tag) {
    case TAG.NULL:
      return { type: "null" };
    case TAG.BOOL: {
      const b = readByte(r);
      if (b !== 0x00 && b !== 0x01) {
        throw new CanonicalBytesDecodeError(`invalid bool byte: 0x${b.toString(16)}`);
      }
      return { type: "bool", value: b === 0x01 };
    }
    case TAG.INT:
      return { type: "int", value: readI64BE(r) };
    case TAG.UINT:
      return { type: "uint", value: readU64BE(r) };
    case TAG.STRING: {
      const len = readVarint(r);
      const bytes = readBytes(r, Number(len));
      return { type: "string", value: new TextDecoder("utf-8", { fatal: true }).decode(bytes) };
    }
    case TAG.BYTES: {
      const len = readVarint(r);
      const bytes = readBytes(r, Number(len));
      return { type: "bytes", value: bytes };
    }
    case TAG.ARRAY: {
      const count = readVarint(r);
      const items: Value[] = [];
      for (let i = 0n; i < count; i++) {
        items.push(decodeOne(r));
      }
      return { type: "array", value: items };
    }
    case TAG.MAP: {
      const count = readVarint(r);
      const m = new Map<string, Value>();
      for (let i = 0n; i < count; i++) {
        // Key is a String value.
        const key = decodeOne(r);
        if (key.type !== "string") {
          throw new CanonicalBytesDecodeError(
            `map key is not a string: got ${key.type}`,
          );
        }
        const value = decodeOne(r);
        m.set(key.value, value);
      }
      return { type: "map", value: m };
    }
    case TAG.TIMESTAMP:
      return { type: "timestamp", value: readI64BE(r) };
    case TAG.HASH: {
      const bytes = readBytes(r, 32);
      return { type: "hash", value: bytes };
    }
    default:
      throw new CanonicalBytesDecodeError(
        `unknown tag byte: 0x${tag.toString(16)} at offset ${r.offset - 1}`,
      );
  }
}

/**
 * Decode canonical bytes back into a typed Value tree.
 *
 * Per L0 §9.3 + L1_HARD_RULES C18: the decode must be deterministic; given
 * canonical bytes that were produced by encode(), decode() returns a Value
 * tree that re-encodes to identical bytes.
 *
 * @throws {CanonicalBytesDecodeError} on malformed input (unexpected EOF,
 *   unknown tag, invalid UTF-8 in strings, oversized varint, etc.).
 */
export function decode(canonical: CanonicalBytes): Value {
  const r: Reader = { bytes: canonical.bytes, offset: 0 };
  const v = decodeOne(r);
  if (r.offset !== canonical.bytes.length) {
    throw new CanonicalBytesDecodeError(
      `trailing bytes: ${canonical.bytes.length - r.offset} bytes after decoded value`,
    );
  }
  return v;
}

// ---------------------------------------------------------------------------
// Renderer: Value → human-readable string.
// ---------------------------------------------------------------------------

/** Render options. */
export interface RenderOptions {
  /** Indentation width in spaces (default 2). */
  indent?: number;
  /** Max bytes to show inline before truncating with "...<N bytes>" (default 64). */
  maxBytesInline?: number;
  /** Max string chars to show inline before truncating (default 200). */
  maxStringInline?: number;
}

const DEFAULT_OPTIONS: Required<RenderOptions> = {
  indent: 2,
  maxBytesInline: 64,
  maxStringInline: 200,
};

/**
 * Render a Value tree as a deterministic human-readable string.
 *
 * Per L0 §9.3 + L1_HARD_RULES C18: two anchor_client instances rendering
 * the same canonical bytes MUST produce identical text output. This is the
 * substrate-to-owner display channel; the owner reviews the rendered text
 * before signing.
 *
 * Format:
 *
 *     {  "field_name": <rendered_value>,  ... }
 *
 * For maps and arrays, contents are indented. Bytes are shown as
 * lowercase-hex; values longer than `maxBytesInline` are truncated.
 */
export function render(value: Value, options: RenderOptions = {}): string {
  const opts = { ...DEFAULT_OPTIONS, ...options };
  return renderAt(value, 0, opts);
}

function renderAt(value: Value, depth: number, opts: Required<RenderOptions>): string {
  const indent = " ".repeat(depth * opts.indent);
  const innerIndent = " ".repeat((depth + 1) * opts.indent);

  switch (value.type) {
    case "null":
      return "null";
    case "bool":
      return value.value ? "true" : "false";
    case "int":
      return value.value.toString();
    case "uint":
      return `${value.value}u`;
    case "string": {
      const s = value.value;
      if (s.length > opts.maxStringInline) {
        return `"${s.substring(0, opts.maxStringInline)}…<${s.length - opts.maxStringInline} chars>"`;
      }
      return JSON.stringify(s);
    }
    case "bytes": {
      const hex = bytesToHex(value.value);
      if (value.value.length > opts.maxBytesInline) {
        return `0x${hex.substring(0, opts.maxBytesInline * 2)}…<${value.value.length - opts.maxBytesInline} bytes>`;
      }
      return `0x${hex}`;
    }
    case "hash":
      return `hash:0x${bytesToHex(value.value)}`;
    case "timestamp":
      return `ts:${value.value}`;
    case "array": {
      if (value.value.length === 0) return "[]";
      const items = value.value.map(
        (item) => `${innerIndent}${renderAt(item, depth + 1, opts)}`,
      );
      return `[\n${items.join(",\n")}\n${indent}]`;
    }
    case "map": {
      if (value.value.size === 0) return "{}";
      // Sort by key for deterministic output (matches canonical-bytes ordering
      // for string keys — which is the same as JavaScript string sort for ASCII;
      // for non-ASCII the canonical_bytes module sorts by encoded-bytes, so this
      // render-time sort uses the same comparator).
      const sortedKeys = Array.from(value.value.keys()).sort();
      const entries = sortedKeys.map((key) => {
        const v = value.value.get(key)!;
        const renderedKey = JSON.stringify(key);
        const renderedValue = renderAt(v, depth + 1, opts);
        return `${innerIndent}${renderedKey}: ${renderedValue}`;
      });
      return `{\n${entries.join(",\n")}\n${indent}}`;
    }
  }
}

function bytesToHex(bytes: Uint8Array): string {
  let s = "";
  for (const b of bytes) {
    s += b.toString(16).padStart(2, "0");
  }
  return s;
}

// ---------------------------------------------------------------------------
// High-level convenience: decode + render in one pass.
// ---------------------------------------------------------------------------

/**
 * Decode canonical bytes and render them for owner review.
 *
 * Used by the anchor-surface client when displaying a proposed mutation:
 *
 *     1. Substrate emits AttestationRequest with canonical_bytes payload.
 *     2. anchor_client.renderForReview(payload) → human-readable text.
 *     3. Owner reads, signs the canonical_bytes hash.
 */
export function renderForReview(
  canonical: CanonicalBytes,
  options: RenderOptions = {},
): string {
  const value = decode(canonical);
  return render(value, options);
}
