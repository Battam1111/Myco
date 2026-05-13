// Tests for renderer.ts — decode + render round-trips.

import { test } from "node:test";
import { strict as assert } from "node:assert";

import { CanonicalBytes, encode, type Value } from "../src/canonical_bytes.ts";
import {
  CanonicalBytesDecodeError,
  decode,
  render,
  renderForReview,
} from "../src/renderer.ts";

// ---------------------------------------------------------------------------
// Round-trip property: encode → decode → re-encode produces identical bytes.
// ---------------------------------------------------------------------------

function roundTrip(v: Value): void {
  const cb1 = encode(v);
  const decoded = decode(cb1);
  const cb2 = encode(decoded);
  assert.equal(
    cb1.toHex(),
    cb2.toHex(),
    `round-trip mismatch for ${JSON.stringify(v, (_, val) =>
      typeof val === "bigint" ? val.toString() : val,
    )}`,
  );
}

test("round-trip: null", () => roundTrip({ type: "null" }));
test("round-trip: bool true", () => roundTrip({ type: "bool", value: true }));
test("round-trip: bool false", () => roundTrip({ type: "bool", value: false }));
test("round-trip: int 0", () => roundTrip({ type: "int", value: 0n }));
test("round-trip: int -1", () => roundTrip({ type: "int", value: -1n }));
test("round-trip: int max positive", () =>
  roundTrip({ type: "int", value: (1n << 63n) - 1n }));
test("round-trip: int min negative", () =>
  roundTrip({ type: "int", value: -(1n << 63n) }));
test("round-trip: uint 0", () => roundTrip({ type: "uint", value: 0n }));
test("round-trip: uint max", () =>
  roundTrip({ type: "uint", value: (1n << 64n) - 1n }));
test("round-trip: string empty", () => roundTrip({ type: "string", value: "" }));
test("round-trip: string hello", () =>
  roundTrip({ type: "string", value: "hello" }));
test("round-trip: string unicode emoji", () =>
  roundTrip({ type: "string", value: "🍄" }));
test("round-trip: string unicode chinese", () =>
  roundTrip({ type: "string", value: "你好" }));
test("round-trip: bytes empty", () =>
  roundTrip({ type: "bytes", value: new Uint8Array(0) }));
test("round-trip: bytes 128 zeros", () =>
  roundTrip({ type: "bytes", value: new Uint8Array(128) }));
test("round-trip: array empty", () =>
  roundTrip({ type: "array", value: [] }));
test("round-trip: array two ints", () =>
  roundTrip({
    type: "array",
    value: [
      { type: "int", value: 1n },
      { type: "int", value: 2n },
    ],
  }));
test("round-trip: map empty", () =>
  roundTrip({ type: "map", value: new Map() }));
test("round-trip: map sorted keys", () =>
  roundTrip({
    type: "map",
    value: new Map([
      ["z", { type: "int", value: 1n } as Value],
      ["a", { type: "int", value: 2n }],
      ["m", { type: "int", value: 3n }],
    ]),
  }));
test("round-trip: nested map", () =>
  roundTrip({
    type: "map",
    value: new Map([
      [
        "outer",
        {
          type: "map",
          value: new Map([["inner", { type: "uint", value: 42n } as Value]]),
        } as Value,
      ],
    ]),
  }));
test("round-trip: timestamp", () =>
  roundTrip({ type: "timestamp", value: 1_700_000_000_000_000_000n }));
test("round-trip: hash", () =>
  roundTrip({ type: "hash", value: new Uint8Array(32).fill(0xab) }));

// ---------------------------------------------------------------------------
// Decode error cases.
// ---------------------------------------------------------------------------

test("decode error: unknown tag", () => {
  const bad = new CanonicalBytes(new Uint8Array([0xff]));
  assert.throws(() => decode(bad), CanonicalBytesDecodeError);
});

test("decode error: truncated input", () => {
  // Tag 0x10 (INT) needs 8 bytes; provide 3.
  const bad = new CanonicalBytes(new Uint8Array([0x10, 0x00, 0x01, 0x02]));
  assert.throws(() => decode(bad), CanonicalBytesDecodeError);
});

test("decode error: trailing bytes", () => {
  // Valid null (0x00) followed by an extra byte.
  const bad = new CanonicalBytes(new Uint8Array([0x00, 0xff]));
  assert.throws(() => decode(bad), /trailing bytes/);
});

test("decode error: map key not a string", () => {
  // Map with count=1 + key=Null + value=Null → invalid.
  const bad = new CanonicalBytes(new Uint8Array([0x31, 0x01, 0x00, 0x00]));
  assert.throws(() => decode(bad), /map key is not a string/);
});

test("decode error: invalid bool byte", () => {
  const bad = new CanonicalBytes(new Uint8Array([0x01, 0x05]));
  assert.throws(() => decode(bad), /invalid bool byte/);
});

// ---------------------------------------------------------------------------
// Render: human-readable output is deterministic.
// ---------------------------------------------------------------------------

test("render null", () => {
  assert.equal(render({ type: "null" }), "null");
});

test("render bool", () => {
  assert.equal(render({ type: "bool", value: true }), "true");
  assert.equal(render({ type: "bool", value: false }), "false");
});

test("render int", () => {
  assert.equal(render({ type: "int", value: 42n }), "42");
  assert.equal(render({ type: "int", value: -1n }), "-1");
});

test("render uint with suffix", () => {
  assert.equal(render({ type: "uint", value: 42n }), "42u");
});

test("render string with JSON escaping", () => {
  assert.equal(render({ type: "string", value: 'hello "world"' }), '"hello \\"world\\""');
});

test("render bytes as hex with 0x prefix", () => {
  assert.equal(
    render({ type: "bytes", value: new Uint8Array([0xab, 0xcd]) }),
    "0xabcd",
  );
});

test("render bytes truncation when over maxBytesInline", () => {
  const bytes = new Uint8Array(128);
  const r = render({ type: "bytes", value: bytes }, { maxBytesInline: 8 });
  assert.match(r, /^0x0+…<120 bytes>$/);
});

test("render hash with prefix", () => {
  const r = render({ type: "hash", value: new Uint8Array(32).fill(0xab) });
  assert.equal(r, `hash:0x${"ab".repeat(32)}`);
});

test("render timestamp with prefix", () => {
  assert.equal(render({ type: "timestamp", value: 1700000000n }), "ts:1700000000");
});

test("render empty array", () => {
  assert.equal(render({ type: "array", value: [] }), "[]");
});

test("render array with items indents", () => {
  const r = render(
    {
      type: "array",
      value: [
        { type: "int", value: 1n },
        { type: "int", value: 2n },
      ],
    },
    { indent: 2 },
  );
  assert.equal(r, "[\n  1,\n  2\n]");
});

test("render empty map", () => {
  assert.equal(render({ type: "map", value: new Map() }), "{}");
});

test("render map sorts keys", () => {
  const m = new Map<string, Value>([
    ["z", { type: "int", value: 1n }],
    ["a", { type: "int", value: 2n }],
    ["m", { type: "int", value: 3n }],
  ]);
  const r = render({ type: "map", value: m });
  // Keys should be rendered in sorted order: a, m, z.
  const aIdx = r.indexOf('"a"');
  const mIdx = r.indexOf('"m"');
  const zIdx = r.indexOf('"z"');
  assert.ok(aIdx < mIdx);
  assert.ok(mIdx < zIdx);
});

test("render is deterministic — same input → same output", () => {
  const v: Value = {
    type: "map",
    value: new Map([
      ["b", { type: "bool", value: true } as Value],
      ["a", { type: "int", value: 1n }],
    ]),
  };
  assert.equal(render(v), render(v));
});

// ---------------------------------------------------------------------------
// renderForReview: decode + render together.
// ---------------------------------------------------------------------------

test("renderForReview decodes and renders", () => {
  const v: Value = { type: "string", value: "review me" };
  const cb = encode(v);
  const text = renderForReview(cb);
  assert.equal(text, '"review me"');
});

test("renderForReview on map produces same text as render(decode(...))", () => {
  const v: Value = {
    type: "map",
    value: new Map([
      ["k1", { type: "uint", value: 100n } as Value],
      ["k2", { type: "string", value: "v2" }],
    ]),
  };
  const cb = encode(v);
  const fromReview = renderForReview(cb);
  const fromDecode = render(decode(cb));
  assert.equal(fromReview, fromDecode);
});

// ---------------------------------------------------------------------------
// L1_HARD_RULES C18 detection: two render passes on identical canonical bytes
// must produce identical text.
// ---------------------------------------------------------------------------

test("L1_HARD_RULES C18: identical canonical bytes → identical render", () => {
  const v: Value = {
    type: "map",
    value: new Map([
      ["payload", { type: "bytes", value: new Uint8Array([1, 2, 3, 4]) } as Value],
      ["nonce", { type: "hash", value: new Uint8Array(32).fill(0xaa) }],
      ["count", { type: "uint", value: 42n }],
    ]),
  };
  const cb = encode(v);
  const text1 = renderForReview(cb);
  const text2 = renderForReview(cb);
  assert.equal(text1, text2);
});
