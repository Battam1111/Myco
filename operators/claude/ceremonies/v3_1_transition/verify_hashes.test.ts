// Verify the v3.1 transition manifest reproduces from the current bundle.
//
// This test is a CI gate:
//   - PASS = `manifest.json` matches the current `docs/architecture/L0/`
//     bundle bit-for-bit (every file's SHA-256 + the bundle BLAKE3).
//   - FAIL = either someone modified an L0 file without re-running
//     `compute_hashes.ts` (drift), OR `compute_hashes.ts` itself broke
//     (canonical-bytes regression — L1/HARD_RULES C18 territory).
//
// The shared assertions live in ../_lib/ceremony.ts::verifyManifest; this file
// adds the GENESIS-specific extras (the commit/path prior_l0 shape + the
// git-show SHA-256 byte_length check) that the amendments don't have.
//
// NOTE: this v3.1 (genesis) verify test is NOT registered in `npm test` — it
// would fail by design after each subsequent amendment landed (its manifest is
// the HISTORICAL pinned record of the v3.1 moment). The ACTIVE drift gate is
// v3_1_1_1_p03_descriptive_amendment/verify_hashes.test.ts. This file remains
// runnable on demand for archival reproducibility checks against the v3.1 era.

import { describe, it } from "node:test";
import { strict as assert } from "node:assert";

import { loadManifest, verifyManifest } from "../_lib/verify.ts";
import { config, PRIOR_L0_COMMIT, PRIOR_L0_PATH, getPriorL0Hash } from "./config.ts";

const manifest = loadManifest(config.dir);

// Shared assertions (schema_version, ceremony name, diff_summary, new_l0_hash,
// per-file SHA-256, generic prior-hash reproduction).
verifyManifest(config, manifest);

// Genesis-specific extras (verbatim from the original test).
describe("v3.1-stratigraphy transition — genesis-specific manifest checks", () => {
  it("manifest.prior_l0 fields match the pinned commit + path", () => {
    const prior = manifest.prior_l0 as { commit: string; path: string };
    assert.equal(prior.commit, PRIOR_L0_COMMIT);
    assert.equal(prior.path, PRIOR_L0_PATH);
  });

  it("prior_l0_hash reproduces from git show e796451:L0_VISION.md", () => {
    const prior = manifest.prior_l0 as {
      byte_length: number;
      sha256_hex: string;
    };
    const computed = getPriorL0Hash();
    assert.equal(
      computed.byteLength,
      prior.byte_length,
      `prior L0 byte length drifted: manifest=${prior.byte_length} computed=${computed.byteLength}`,
    );
    assert.equal(
      computed.hashHex,
      prior.sha256_hex,
      `prior_l0_hash drift: manifest=${prior.sha256_hex} computed=${computed.hashHex}`,
    );
  });
});
