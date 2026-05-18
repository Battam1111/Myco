// Framing tests — FrameReader + encodeFrame edge cases.

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  encodeFrame,
  FrameReader,
} from "../src/protocol/framing.ts";
import { FrameTooLargeError, MAX_FRAME_BODY_SIZE } from "../src/protocol/messages.ts";

describe("encodeFrame", () => {
  it("prepends u32 BE length", () => {
    const body = new Uint8Array([1, 2, 3, 4, 5]);
    const wire = encodeFrame(body);
    assert.equal(wire.length, 4 + 5);
    assert.equal(wire[0], 0);
    assert.equal(wire[1], 0);
    assert.equal(wire[2], 0);
    assert.equal(wire[3], 5);
    assert.deepEqual(wire.subarray(4), body);
  });

  it("handles empty body", () => {
    const wire = encodeFrame(new Uint8Array(0));
    assert.deepEqual(Array.from(wire), [0, 0, 0, 0]);
  });

  it("rejects oversized body", () => {
    const huge = new Uint8Array(MAX_FRAME_BODY_SIZE + 1);
    assert.throws(() => encodeFrame(huge), FrameTooLargeError);
  });
});

describe("FrameReader", () => {
  it("reads a single frame fed in one chunk", () => {
    const body = new Uint8Array([10, 20, 30]);
    const reader = new FrameReader();
    reader.push(encodeFrame(body));
    const got = reader.tryReadFrame();
    assert.deepEqual(got, body);
    assert.equal(reader.tryReadFrame(), null);
  });

  it("reads a frame split across multiple chunks", () => {
    const body = new Uint8Array([1, 2, 3, 4, 5, 6, 7, 8]);
    const wire = encodeFrame(body);
    const reader = new FrameReader();
    // Feed byte-by-byte.
    for (const b of wire) {
      reader.push(new Uint8Array([b]));
    }
    const got = reader.tryReadFrame();
    assert.deepEqual(got, body);
  });

  it("reads two concatenated frames", () => {
    const a = new Uint8Array([1, 2]);
    const b = new Uint8Array([3, 4, 5]);
    const reader = new FrameReader();
    reader.push(encodeFrame(a));
    reader.push(encodeFrame(b));
    assert.deepEqual(reader.tryReadFrame(), a);
    assert.deepEqual(reader.tryReadFrame(), b);
    assert.equal(reader.tryReadFrame(), null);
  });

  it("returns null when only partial length prefix is available", () => {
    const reader = new FrameReader();
    reader.push(new Uint8Array([0, 0])); // 2 of 4 bytes
    assert.equal(reader.tryReadFrame(), null);
  });

  it("returns null when length prefix is complete but body is partial", () => {
    const reader = new FrameReader();
    reader.push(new Uint8Array([0, 0, 0, 10])); // says 10 bytes follow
    reader.push(new Uint8Array([1, 2, 3])); // only 3 of 10
    assert.equal(reader.tryReadFrame(), null);
    // Should be able to complete with the remaining bytes.
    reader.push(new Uint8Array([4, 5, 6, 7, 8, 9, 10]));
    const got = reader.tryReadFrame();
    assert.deepEqual(got, new Uint8Array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]));
  });

  it("rejects oversized incoming frame", () => {
    const reader = new FrameReader();
    const lengthBytes = new Uint8Array(4);
    const huge = MAX_FRAME_BODY_SIZE + 1;
    lengthBytes[0] = (huge >>> 24) & 0xff;
    lengthBytes[1] = (huge >>> 16) & 0xff;
    lengthBytes[2] = (huge >>> 8) & 0xff;
    lengthBytes[3] = huge & 0xff;
    reader.push(lengthBytes);
    assert.throws(() => reader.tryReadFrame(), FrameTooLargeError);
  });
});
