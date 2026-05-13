// Cross-language parity test for canonical-bytes serializer.
//
// Loads `test_vectors/canonical_bytes_v1.json` and verifies that the
// TypeScript implementation produces byte-identical output to the spec.
// Same JSON file is consumed by Rust + Python implementations.

import { test } from "node:test";
import { strict as assert } from "node:assert";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import {
  encode,
  writeVarint,
  type Value,
  CanonicalBytes,
} from "../src/canonical_bytes.ts";

// Locate test_vectors/canonical_bytes_v1.json relative to this file.
const __dirname = dirname(fileURLToPath(import.meta.url));
const vectorsPath = join(__dirname, "..", "..", "test_vectors", "canonical_bytes_v1.json");
const vectorsRaw = readFileSync(vectorsPath, "utf-8");
const vectors = JSON.parse(vectorsRaw) as TestVectorsFile;

/** Shape of the canonical_bytes_v1.json file. */
interface TestVectorsFile {
  version: number;
  vectors: VectorCase[];
  varint_vectors: VarintCase[];
}

interface VectorCase {
  name: string;
  input: InputSpec;
  output_hex: string;
}

interface VarintCase {
  input: number;
  output_hex: string;
}

/** JSON encoding of `Value` inputs in the test vectors file. */
type InputSpec =
  | { type: "null" }
  | { type: "bool"; value: boolean }
  | { type: "int"; value?: number; value_decimal_str?: string }
  | { type: "uint"; value?: number; value_decimal_str?: string }
  | { type: "string"; value?: string; value_utf8_hex?: string }
  | {
      type: "bytes";
      value_hex?: string;
      value_hex_repeat?: { byte: string; count: number };
    }
  | { type: "array"; value: InputSpec[] }
  | { type: "map"; value: Record<string, InputSpec> }
  | { type: "timestamp"; value?: number; value_decimal_str?: string }
  | { type: "hash"; value_hex: string };

/** Convert a test-vector InputSpec into a runtime Value. */
function loadValue(spec: InputSpec): Value {
  switch (spec.type) {
    case "null":
      return { type: "null" };
    case "bool":
      return { type: "bool", value: spec.value };
    case "int": {
      const v = spec.value_decimal_str !== undefined
        ? BigInt(spec.value_decimal_str)
        : BigInt(spec.value!);
      return { type: "int", value: v };
    }
    case "uint": {
      const v = spec.value_decimal_str !== undefined
        ? BigInt(spec.value_decimal_str)
        : BigInt(spec.value!);
      return { type: "uint", value: v };
    }
    case "string": {
      let s: string;
      if (spec.value !== undefined) {
        s = spec.value;
      } else if (spec.value_utf8_hex !== undefined) {
        s = new TextDecoder("utf-8", { fatal: true }).decode(
          hexToBytes(spec.value_utf8_hex),
        );
      } else {
        throw new Error("string case missing value/value_utf8_hex");
      }
      return { type: "string", value: s };
    }
    case "bytes": {
      let bytes: Uint8Array;
      if (spec.value_hex !== undefined) {
        bytes = hexToBytes(spec.value_hex);
      } else if (spec.value_hex_repeat !== undefined) {
        const b = parseInt(spec.value_hex_repeat.byte, 16);
        bytes = new Uint8Array(spec.value_hex_repeat.count).fill(b);
      } else {
        throw new Error("bytes case missing value_hex/value_hex_repeat");
      }
      return { type: "bytes", value: bytes };
    }
    case "array":
      return { type: "array", value: spec.value.map(loadValue) };
    case "map": {
      const m = new Map<string, Value>();
      for (const [k, v] of Object.entries(spec.value)) {
        m.set(k, loadValue(v));
      }
      return { type: "map", value: m };
    }
    case "timestamp": {
      const v = spec.value_decimal_str !== undefined
        ? BigInt(spec.value_decimal_str)
        : BigInt(spec.value!);
      return { type: "timestamp", value: v };
    }
    case "hash":
      return { type: "hash", value: hexToBytes(spec.value_hex) };
  }
}

function hexToBytes(hex: string): Uint8Array {
  if (hex.length % 2 !== 0) throw new Error(`odd hex length: ${hex.length}`);
  const out = new Uint8Array(hex.length / 2);
  for (let i = 0; i < out.length; i++) {
    out[i] = parseInt(hex.substring(i * 2, i * 2 + 2), 16);
  }
  return out;
}

// Generate one test per vector.
for (const v of vectors.vectors) {
  test(`canonical_bytes: ${v.name}`, () => {
    const value = loadValue(v.input);
    const got = encode(value);
    assert.equal(
      got.toHex(),
      v.output_hex,
      `vector "${v.name}" mismatch:\n  expected: ${v.output_hex}\n  got:      ${got.toHex()}`,
    );
  });
}

// Generate one test per varint case.
for (const vv of vectors.varint_vectors) {
  test(`varint: ${vv.input}`, () => {
    const buf: number[] = [];
    writeVarint(vv.input, buf);
    const got = new CanonicalBytes(new Uint8Array(buf));
    assert.equal(
      got.toHex(),
      vv.output_hex,
      `varint(${vv.input}) mismatch:\n  expected: ${vv.output_hex}\n  got:      ${got.toHex()}`,
    );
  });
}

// Determinism: encoding the same value twice gives identical bytes.
test("determinism: same input → identical output", () => {
  const v: Value = {
    type: "map",
    value: new Map([
      ["a", { type: "bool", value: true }],
      ["b", { type: "int", value: 42n }],
      [
        "c",
        {
          type: "array",
          value: [{ type: "null" }, { type: "string", value: "x" }],
        },
      ],
    ]),
  };
  const cb1 = encode(v);
  const cb2 = encode(v);
  assert.equal(cb1.toHex(), cb2.toHex());
});

// Error case: hash with wrong length.
test("error: hash with non-32-byte length", () => {
  assert.throws(
    () =>
      encode({
        type: "hash",
        value: new Uint8Array(16), // wrong length
      }),
    /hash must be exactly 32 bytes/,
  );
});

// Error case: varint negative.
test("error: varint negative", () => {
  assert.throws(() => writeVarint(-1, []), /varint cannot encode negative/);
});

// Error case: i64 out of range.
test("error: int out of i64 range", () => {
  assert.throws(
    () =>
      encode({
        type: "int",
        value: (1n << 63n), // i64::MAX + 1
      }),
    /i64 out of range/,
  );
});

// Error case: u64 out of range.
test("error: uint negative", () => {
  assert.throws(
    () =>
      encode({
        type: "uint",
        value: -1n,
      }),
    /u64 out of range/,
  );
});
