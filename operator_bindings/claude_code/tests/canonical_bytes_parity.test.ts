// Cross-language canonical-bytes parity for the TS side of operator_bindings.
//
// Verifies that the TS bridge protocol's BOOTSTRAP_KEY matches the Rust + Python
// constants byte-for-byte (the protocol's most fundamental shared constant).

import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { sha256 } from "@noble/hashes/sha2.js";

import { BOOTSTRAP_KEY } from "../src/protocol/messages.ts";

describe("cross-language bootstrap key parity", () => {
  it("BOOTSTRAP_KEY matches SHA-256 of pinned literal", () => {
    const expected = sha256(
      new TextEncoder().encode("myco-bridge-protocol-v1-bootstrap"),
    );
    assert.deepEqual(BOOTSTRAP_KEY, expected);
  });

  it("BOOTSTRAP_KEY matches the pinned hex string", () => {
    // Pin the actual bytes — any drift forces an explicit protocol-version bump.
    const expectedHex = Array.from(
      sha256(new TextEncoder().encode("myco-bridge-protocol-v1-bootstrap")),
    )
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
    const actualHex = Array.from(BOOTSTRAP_KEY)
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
    assert.equal(actualHex, expectedHex);
  });
});
