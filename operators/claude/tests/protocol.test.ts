// Bridge protocol tests — body + frame roundtrip; HMAC verification.

import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { sha256 } from "@noble/hashes/sha2.js";

import {
  advancePayload,
  BOOTSTRAP_KEY,
  bodyToCanonicalBytes,
  buildOwnerObjectiveCanonicalBytes,
  canonicalBytesToBody,
  computeHmac,
  decodeFrameBody,
  emptyPayload,
  encodeFrameBody,
  floatRepr,
  helloPayload,
  HmacMismatchError,
  type Message,
  MSG_TYPE,
  parseAdvanceResponse,
  parseHelloAck,
  parseSnapshotResponse,
  perturbPayload,
  PROTOCOL_VERSION,
  registerAxisPayload,
} from "../src/protocol/messages.ts";
import { encode as cbEncode, type Value } from "../src/canonical/canonical_bytes.ts";

describe("BOOTSTRAP_KEY", () => {
  it("is 32 bytes", () => {
    assert.equal(BOOTSTRAP_KEY.length, 32);
  });

  it("matches SHA-256 of literal pin string", () => {
    const expected = sha256(
      new TextEncoder().encode("myco-bridge-protocol-v1-bootstrap"),
    );
    assert.deepEqual(BOOTSTRAP_KEY, expected);
  });
});

describe("floatRepr", () => {
  it("integer-valued formats with .0 suffix", () => {
    assert.equal(floatRepr(0), "0.0");
    assert.equal(floatRepr(1), "1.0");
    assert.equal(floatRepr(-2), "-2.0");
  });
  it("fractional uses default String", () => {
    assert.equal(floatRepr(2.5), "2.5");
    assert.equal(floatRepr(-0.125), "-0.125");
  });
  it("special values", () => {
    assert.equal(floatRepr(NaN), "nan");
    assert.equal(floatRepr(Infinity), "inf");
    assert.equal(floatRepr(-Infinity), "-inf");
  });
  it("parses back roundtrip", () => {
    for (const f of [0, 1, -1, 2.5, -0.125, 1e10, 1e-10]) {
      const s = floatRepr(f);
      assert.equal(parseFloat(s), f, `roundtrip drift for ${f}`);
    }
  });
});

describe("buildOwnerObjectiveCanonicalBytes (M26.4 F20 Rust parity)", () => {
  // Byte-parity guard for the owner_objective_declaration content payload.
  // The substrate (Rust `encode_owner_objective`) and this TS builder MUST
  // produce identical canonical-bytes for the same OwnerObjective, or the CI
  // attestation signature fails on the substrate side (C5 / C18). The fixture
  // below is the EXACT inline Map the substrate_client.test.ts e2e builds
  // (the "M26.4: owner_objective_declaration ... accepted" case) — reproducing
  // it here pins the wire shape independently of the live e2e.

  it("byte-equals the inline e2e objective Map (axis_perturbed:0.75 / raw_material:0.25)", () => {
    // ---- Inline Map, copied from substrate_client.test.ts ~3895-3917 ----
    const objectiveMap = new Map<string, Value>();
    objectiveMap.set("objective_id", {
      type: "string",
      value: "m26_4_ts_e2e_objective",
    });
    objectiveMap.set("declared_at_cycle", { type: "uint", value: 0n });
    const weightEntry1 = new Map<string, Value>();
    weightEntry1.set("prefix", { type: "string", value: "axis_perturbed:" });
    weightEntry1.set("weight_repr", { type: "string", value: "0.75" });
    const weightEntry2 = new Map<string, Value>();
    weightEntry2.set("prefix", { type: "string", value: "raw_material:" });
    weightEntry2.set("weight_repr", { type: "string", value: "0.25" });
    objectiveMap.set("weights", {
      type: "array",
      value: [
        { type: "map", value: weightEntry1 },
        { type: "map", value: weightEntry2 },
      ],
    });
    const inlineBytes = cbEncode({ type: "map", value: objectiveMap }).bytes;

    // ---- Builder under test ----
    const builtBytes = buildOwnerObjectiveCanonicalBytes({
      objectiveId: "m26_4_ts_e2e_objective",
      declaredAtCycle: 0n,
      weights: [
        { prefix: "axis_perturbed:", weight: 0.75 },
        { prefix: "raw_material:", weight: 0.25 },
      ],
    });

    assert.deepEqual(
      builtBytes,
      inlineBytes,
      "buildOwnerObjectiveCanonicalBytes must byte-match the inline e2e Map (Rust encode_owner_objective parity)",
    );
  });

  it("renders weights as repr-float STRINGS via floatRepr (not raw String(n))", () => {
    // weight_repr is a String value carrying floatRepr(weight). For an
    // integer-valued weight this is "1.0", NOT "1" — guarding against a
    // String(n) regression that would silently drift the bytes.
    const built = buildOwnerObjectiveCanonicalBytes({
      objectiveId: "ints",
      declaredAtCycle: 7n,
      weights: [{ prefix: "sporocarp:", weight: 1 }],
    });
    const expectMap = new Map<string, Value>();
    expectMap.set("objective_id", { type: "string", value: "ints" });
    expectMap.set("declared_at_cycle", { type: "uint", value: 7n });
    const e = new Map<string, Value>();
    e.set("prefix", { type: "string", value: "sporocarp:" });
    e.set("weight_repr", { type: "string", value: floatRepr(1) }); // "1.0"
    expectMap.set("weights", {
      type: "array",
      value: [{ type: "map", value: e }],
    });
    assert.deepEqual(built, cbEncode({ type: "map", value: expectMap }).bytes);
    assert.equal(floatRepr(1), "1.0"); // explicit: the value that's embedded
  });

  it("empty weights builds (substrate enforces non-empty, not the builder)", () => {
    // The builder itself does not reject empty weights — the substrate emits
    // C5 for that. Here we only assert the empty-array shape encodes cleanly.
    const built = buildOwnerObjectiveCanonicalBytes({
      objectiveId: "empty",
      declaredAtCycle: 0n,
      weights: [],
    });
    const m = new Map<string, Value>();
    m.set("objective_id", { type: "string", value: "empty" });
    m.set("declared_at_cycle", { type: "uint", value: 0n });
    m.set("weights", { type: "array", value: [] });
    assert.deepEqual(built, cbEncode({ type: "map", value: m }).bytes);
  });
});

describe("body roundtrip", () => {
  function roundtripBody(message: Message): void {
    const cb = bodyToCanonicalBytes(message);
    const decoded = canonicalBytesToBody(cb.bytes);
    assert.equal(decoded.messageType, message.messageType);
    assert.equal(decoded.requestId, message.requestId);
    assert.equal(decoded.version, PROTOCOL_VERSION);
    // Compare by re-encoding (Map iteration order differs between
    // insertion-order and canonical-bytes-order).
    const recoded = bodyToCanonicalBytes(decoded);
    assert.deepEqual(recoded.bytes, cb.bytes);
  }

  it("hello roundtrips", () => {
    roundtripBody({
      version: 1n,
      messageType: MSG_TYPE.HELLO,
      requestId: 1n,
      payload: helloPayload(new Uint8Array(32).fill(0x42)),
    });
  });

  it("register_axis appetite roundtrips", () => {
    roundtripBody({
      version: 1n,
      messageType: MSG_TYPE.REGISTER_AXIS,
      requestId: 10n,
      payload: registerAxisPayload({
        name: "curiosity",
        axisClass: "appetite",
        fruitingThreshold: 5.0,
        initialValue: 0.0,
        decayRatePerCycle: 1.0,
        isMortalitySignal: false,
        updateRuleKind: "noop",
      }),
    });
  });

  it("register_axis decay (mortality) roundtrips", () => {
    roundtripBody({
      version: 1n,
      messageType: MSG_TYPE.REGISTER_AXIS,
      requestId: 11n,
      payload: registerAxisPayload({
        name: "mortality",
        axisClass: "decay",
        fruitingThreshold: 0.1,
        initialValue: 1.0,
        decayRatePerCycle: 0.5,
        isMortalitySignal: true,
        updateRuleKind: "decay",
      }),
    });
  });

  it("perturb roundtrips", () => {
    roundtripBody({
      version: 1n,
      messageType: MSG_TYPE.PERTURB,
      requestId: 100n,
      payload: perturbPayload("x", 2.5),
    });
  });

  it("advance roundtrips", () => {
    roundtripBody({
      version: 1n,
      messageType: MSG_TYPE.ADVANCE,
      requestId: 200n,
      payload: advancePayload(7n),
    });
  });

  it("snapshot roundtrips", () => {
    roundtripBody({
      version: 1n,
      messageType: MSG_TYPE.SNAPSHOT,
      requestId: 300n,
      payload: emptyPayload(),
    });
  });

  it("shutdown roundtrips", () => {
    roundtripBody({
      version: 1n,
      messageType: MSG_TYPE.SHUTDOWN,
      requestId: 999n,
      payload: emptyPayload(),
    });
  });
});

describe("frame encode/decode", () => {
  it("roundtrips with session key", () => {
    const key = new Uint8Array(32).fill(0xee);
    const msg: Message = {
      version: 1n,
      messageType: MSG_TYPE.ADVANCE,
      requestId: 5n,
      payload: advancePayload(11n),
    };
    const frame = encodeFrameBody(msg, key);
    const decoded = decodeFrameBody(frame, key);
    assert.equal(decoded.messageType, MSG_TYPE.ADVANCE);
    assert.equal(decoded.requestId, 5n);
  });

  it("roundtrips with bootstrap key", () => {
    const msg: Message = {
      version: 1n,
      messageType: MSG_TYPE.HELLO,
      requestId: 0n,
      payload: helloPayload(new Uint8Array(32).fill(0x01)),
    };
    const frame = encodeFrameBody(msg, BOOTSTRAP_KEY);
    const decoded = decodeFrameBody(frame, BOOTSTRAP_KEY);
    assert.equal(decoded.messageType, MSG_TYPE.HELLO);
  });

  it("rejects wrong key", () => {
    const correct = new Uint8Array(32).fill(0xee);
    const wrong = new Uint8Array(32).fill(0x11);
    const msg: Message = {
      version: 1n,
      messageType: MSG_TYPE.ADVANCE,
      requestId: 5n,
      payload: advancePayload(11n),
    };
    const frame = encodeFrameBody(msg, correct);
    assert.throws(() => decodeFrameBody(frame, wrong), HmacMismatchError);
  });

  it("rejects corrupted body", () => {
    const key = new Uint8Array(32).fill(0xee);
    const msg: Message = {
      version: 1n,
      messageType: MSG_TYPE.ADVANCE,
      requestId: 5n,
      payload: advancePayload(11n),
    };
    const frame = encodeFrameBody(msg, key);
    frame[40] ^= 0x01;
    assert.throws(() => decodeFrameBody(frame, key), HmacMismatchError);
  });

  it("rejects too-small frame", () => {
    assert.throws(() =>
      decodeFrameBody(new Uint8Array(10), BOOTSTRAP_KEY),
    );
  });
});

describe("computeHmac", () => {
  it("rejects empty key", () => {
    assert.throws(() => computeHmac(new Uint8Array([1, 2, 3]), new Uint8Array(0)));
  });

  it("is deterministic", () => {
    const key = new Uint8Array(32).fill(0xee);
    const body = new Uint8Array([1, 2, 3, 4]);
    const h1 = computeHmac(body, key);
    const h2 = computeHmac(body, key);
    assert.deepEqual(h1, h2);
  });
});

describe("response parsers", () => {
  it("parseHelloAck", () => {
    const payload = new Map<string, import("../src/canonical/canonical_bytes.ts").Value>();
    payload.set("kernel_tropism_version", { type: "string", value: "0.9.0" });
    payload.set("python_version", { type: "string", value: "3.13.3" });
    payload.set("substrate_version", { type: "string", value: "0.9.0-alpha.2" });
    const ack = parseHelloAck({
      version: 1n,
      messageType: MSG_TYPE.HELLO_ACK,
      requestId: 1n,
      payload,
    });
    assert.equal(ack.kernelTropismVersion, "0.9.0");
    assert.equal(ack.pythonVersion, "3.13.3");
    assert.equal(ack.substrateVersion, "0.9.0-alpha.2");
  });

  it("parseAdvanceResponse with empty fruit", () => {
    const payload = new Map<string, import("../src/canonical/canonical_bytes.ts").Value>();
    payload.set("cycle_number", { type: "uint", value: 3n });
    payload.set("fruited_axes", { type: "array", value: [] });
    payload.set("sporocarps", { type: "array", value: [] });
    const report = parseAdvanceResponse({
      version: 1n,
      messageType: MSG_TYPE.ADVANCE_RESPONSE,
      requestId: 1n,
      payload,
    });
    assert.equal(report.cycleNumber, 3n);
    assert.deepEqual(report.fruitedAxes, []);
    assert.equal(report.sporocarps.length, 0);
  });

  it("parseSnapshotResponse", () => {
    const valuesMap = new Map<string, import("../src/canonical/canonical_bytes.ts").Value>();
    valuesMap.set("a", { type: "string", value: "2.5" });
    valuesMap.set("b", { type: "string", value: "0.0" });
    const payload = new Map<string, import("../src/canonical/canonical_bytes.ts").Value>();
    payload.set("values", { type: "map", value: valuesMap });
    const snap = parseSnapshotResponse({
      version: 1n,
      messageType: MSG_TYPE.SNAPSHOT_RESPONSE,
      requestId: 1n,
      payload,
    });
    assert.equal(snap.get("a"), 2.5);
    assert.equal(snap.get("b"), 0.0);
  });
});
