// Bridge protocol tests — body + frame roundtrip; HMAC verification.

import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { sha256 } from "@noble/hashes/sha2.js";

import {
  advancePayload,
  BOOTSTRAP_KEY,
  bodyToCanonicalBytes,
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
    const payload = new Map<string, import("@myco/anchor-client/src/canonical_bytes.ts").Value>();
    payload.set("kernel_tropism_version", { type: "string", value: "0.9.0" });
    payload.set("python_version", { type: "string", value: "3.13.3" });
    payload.set("substrate_version", { type: "string", value: "0.9.0-alpha.1" });
    const ack = parseHelloAck({
      version: 1n,
      messageType: MSG_TYPE.HELLO_ACK,
      requestId: 1n,
      payload,
    });
    assert.equal(ack.kernelTropismVersion, "0.9.0");
    assert.equal(ack.pythonVersion, "3.13.3");
    assert.equal(ack.substrateVersion, "0.9.0-alpha.1");
  });

  it("parseAdvanceResponse with empty fruit", () => {
    const payload = new Map<string, import("@myco/anchor-client/src/canonical_bytes.ts").Value>();
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
    const valuesMap = new Map<string, import("@myco/anchor-client/src/canonical_bytes.ts").Value>();
    valuesMap.set("a", { type: "string", value: "2.5" });
    valuesMap.set("b", { type: "string", value: "0.0" });
    const payload = new Map<string, import("@myco/anchor-client/src/canonical_bytes.ts").Value>();
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
