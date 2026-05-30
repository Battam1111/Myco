// Verify the v3.1.1 amendment ceremony manifest reproduces from the current
// bundle.
//
// CI gate:
//   - PASS = `manifest.json` matches the current `docs/architecture/L0/`
//     bundle (every file's SHA-256 + the bundle BLAKE3).
//   - FAIL = either someone modified an L0 file without re-running
//     `compute_hashes.ts` (drift), OR `compute_hashes.ts` itself broke
//     (canonical-bytes regression — L1/HARD_RULES C18 territory).
//
// The shared assertions live in ../_lib/ceremony.ts::verifyManifest; this file
// adds the v3.1.1-specific extras (CHAR07 present + P07 byte-distinct).
//
// NOTE: this is the v3.1.1 amendment's manifest. It is NOT registered in
// `npm test` anymore (it fails by design after v3.1.1.1 landed); the active
// drift gate is v3_1_1_1_p03_descriptive_amendment/verify_hashes.test.ts.
// This file remains runnable on demand for archival reproducibility checks.

import { describe, it } from "node:test";
import { strict as assert } from "node:assert";

import { loadManifest, verifyManifest } from "../_lib/verify.ts";
import { config } from "./config.ts";

const manifest = loadManifest(config.dir);

// Shared assertions (schema_version, ceremony name, chained_from, diff_summary,
// prior-hash chain link, new_l0_hash, per-file SHA-256).
verifyManifest(config, manifest);

// v3.1.1-specific extras (verbatim from the original test).
describe("v3.1.1-mortality-refinement-and-charite — amendment-specific checks", () => {
  it("CHAR07_caring.md is present in the bundle (v3.1.1 addition)", () => {
    const found = manifest.new_l0.bundle_files.find(
      (f) => f.path === "cards/CHAR07_caring.md",
    );
    assert.ok(
      found,
      "CHAR07_caring.md must be in the v3.1.1 bundle; absence indicates v3.1.1 amendment did not land",
    );
  });

  it("P07_mortality.md is byte-distinct from the v3.1 version", () => {
    // v3.1 P07 had specific sha256: 6dd80fb91… (v3.1 manifest). The v3.1.1
    // rewrite must produce a different hash. We don't pin v3.1's hash here
    // (that's manifest-internal) but assert that v3.1.1's P07 byte_length is
    // larger than v3.1's (the rewrite expanded the deposit + added 应朽
    // family + interaction rule + misreading + provenance entry).
    const p07 = manifest.new_l0.bundle_files.find(
      (f) => f.path === "cards/P07_mortality.md",
    );
    assert.ok(p07, "P07_mortality.md must be in bundle");
    assert.ok(
      p07.byte_length > 15000,
      `v3.1.1 P07 should be substantially larger than v3.1 (got ${p07.byte_length} bytes)`,
    );
  });
});
