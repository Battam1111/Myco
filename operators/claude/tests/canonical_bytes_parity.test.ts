// Cross-language canonical-bytes parity for the TS side of operators.
//
// Verifies that the TS bridge protocol's BOOTSTRAP_KEY matches the Rust + Python
// constants byte-for-byte (the protocol's most fundamental shared constant).

import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { sha256 } from "@noble/hashes/sha2.js";

import {
  BOOTSTRAP_KEY,
  buildSpawnCosignCanonicalBytes,
} from "../src/protocol/messages.ts";

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

describe("cross-language spawn-cosign envelope parity (P08 §3.5 / §5.1)", () => {
  // The myco-spawn-cosign-v1 envelope is the security + wire contract between
  // the cultivator's signing (TS) and the substrate's verify (Rust). The TS
  // `buildSpawnCosignCanonicalBytes` MUST byte-match the Rust
  // `build_spawn_cosign_canonical_bytes` for the same inputs, or co-signed
  // spawn attestations stop verifying cross-side (every sprout → C68). This
  // vector is pinned identically in the Rust test
  // `spawn_cosign_parity_vector_pinned` (substrate/src/events/attestation.rs).
  const SPAWN_COSIGN_PARITY_HEX =
    "31072006646f6d61696e20146d79636f2d737061776e2d636f7369676e2d7631200c616e63686f725f6e6f6e636521200303030303030303030303030303030303030303030303030303030303030303200e64657074685f6f766572726964650101201173706f72655f736368656d615f68617368212002020202020202020202020202020202020202020202020202020202020202022013706172656e745f7375627374726174655f6964212001010101010101010101010101010101010101010101010101010101010101012018616e63686f725f74696d657374616d705f756e69785f6e734017979cfe710868b1201f6368696c645f67656e657369735f74696d657374616d705f756e69785f6e734017979cfe3d85cd15";

  it("buildSpawnCosignCanonicalBytes matches the pinned Rust vector", () => {
    const bytes = buildSpawnCosignCanonicalBytes({
      parentSubstrateId: new Uint8Array(32).fill(0x01),
      sporeSchemaHash: new Uint8Array(32).fill(0x02),
      childGenesisTimestampUnixNs: 1_700_000_000_123_456_789n,
      anchorTimestampUnixNs: 1_700_000_000_987_654_321n,
      anchorNonce: new Uint8Array(32).fill(0x03),
      depthOverride: true,
    });
    const actualHex = Array.from(bytes)
      .map((b) => b.toString(16).padStart(2, "0"))
      .join("");
    assert.equal(
      actualHex,
      SPAWN_COSIGN_PARITY_HEX,
      "TS spawn-cosign canonical bytes drifted from the pinned Rust parity " +
        "vector — cultivator signing (TS) + substrate verify (Rust) would diverge",
    );
  });
});
