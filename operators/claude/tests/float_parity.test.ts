// Cross-language float-render parity (TypeScript side).
//
// Loads the shared contract `test_vectors/canonical_bytes_v1.json` and verifies
// that the operator's `floatRepr` reproduces the expected CPython `repr()`
// string for every entry in `float_vectors`. The SAME JSON drives the Rust
// (test_vectors/rs) and Python (kernel/governance) float-parity suites — when
// all three pass, the float-rendering wire form is byte-identical across
// languages. Drift = the float facet of L1/HARD_RULES C18
// `canonical_bytes_render_drift` (CRITICAL).
//
// Floats are encoded in canonical-bytes as `String(floatRepr(x))` (there is no
// float tag), so this is the float facet of the canonical-bytes contract.

import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import { floatRepr } from "../src/protocol/messages.ts";

interface FloatCase {
  name: string;
  f64_be_hex: string;
  expected_repr: string;
}

// operators/claude/tests/ -> repo root is three levels up.
const here = dirname(fileURLToPath(import.meta.url));
const vectorsPath = join(
  here,
  "..",
  "..",
  "..",
  "test_vectors",
  "canonical_bytes_v1.json",
);

const vectors = JSON.parse(readFileSync(vectorsPath, "utf8")) as {
  float_vectors: FloatCase[];
};

/** Reconstruct an f64 from its big-endian IEEE-754 bit pattern (16 hex chars). */
function f64FromBeHex(hex: string): number {
  assert.equal(hex.length, 16, `f64_be_hex must be 16 hex chars: ${hex}`);
  const view = new DataView(new ArrayBuffer(8));
  for (let i = 0; i < 8; i++) {
    view.setUint8(i, parseInt(hex.slice(i * 2, i * 2 + 2), 16));
  }
  return view.getFloat64(0, false); // big-endian
}

describe("cross-language float_repr parity", () => {
  it("float_vectors is present and non-empty", () => {
    assert.ok(Array.isArray(vectors.float_vectors));
    assert.ok(vectors.float_vectors.length > 0);
  });

  for (const v of vectors.float_vectors) {
    it(`floatRepr matches CPython repr for "${v.name}"`, () => {
      const f = f64FromBeHex(v.f64_be_hex);
      const got = floatRepr(f);
      assert.equal(
        got,
        v.expected_repr,
        `float vector "${v.name}" mismatch:\n  expected: ${v.expected_repr}\n  got:      ${got}`,
      );
    });
  }
});
