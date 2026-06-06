// Verify the v3.1.5-keyless-anchor-retirement ceremony manifest reproduces from
// the current bundle.
//
// CI gate (THIS is the active drift gate registered in `npm test`):
//   - PASS = `manifest.json` matches the current `docs/architecture/L0/` bundle
//     (every file's SHA-256 + the bundle BLAKE3).
//   - FAIL = an L0 file changed without re-running `compute_hashes.ts` (drift),
//     OR `compute_hashes.ts` broke (canonical-bytes regression — C18).
//
// Shared assertions live in ../_lib/verify.ts::verifyManifest; this file adds
// the v3.1.5-specific extras (AS superseded in place -> 36 files unchanged; the
// re-grounded witness carrier cards present).
//
// Chain: v3.1 -> v3.1.1 -> v3.1.1.1 -> v3.1.1.2 -> v3.1.2 -> v3.1.3 -> v3.1.4
//   -> v3.1.5 (keyless owner-key/anchor retirement). Earlier ceremonies' verify
// tests are NOT registered in npm test (they fail by design after each
// subsequent amendment); v3.1.5's is active.

import { describe, it } from "node:test";
import { strict as assert } from "node:assert";

import { loadManifest, verifyManifest } from "../_lib/verify.ts";
import { config } from "./config.ts";

const manifest = loadManifest(config.dir);

// Shared assertions (schema_version, ceremony name, chained_from, diff_summary,
// prior-hash chain link, new_l0_hash, per-file SHA-256).
verifyManifest(config, manifest);

// v3.1.5-specific extras (the keyless owner-key/anchor retirement).
describe("v3.1.5-keyless-anchor-retirement — amendment-specific checks", () => {
  it("bundle is still exactly 36 files (AS superseded in place; no L0 files added/removed)", () => {
    // The retirement supersedes AS_anchor_surface.md IN PLACE (tombstone) rather
    // than deleting it, so the file/card counts are invariant across the reseal.
    assert.equal(
      manifest.new_l0.bundle_files.length,
      36,
      `expected 36 bundle files; got ${manifest.new_l0.bundle_files.length}`,
    );
  });

  it("the AS tombstone + the re-grounded witness carrier cards are present", () => {
    // AS is Superseded but retained in the bundle; P01/P07/COV06/LB carry the
    // re-grounded keyless witnesses; META carries the §7.8 trust-root headline.
    // Their new per-file SHA-256 is checked by verifyManifest above.
    const expected = [
      "cards/AS_anchor_surface.md",
      "cards/P01_agent_primary.md",
      "cards/P07_mortality.md",
      "cards/COV06_no_abandonment_succession.md",
      "cards/LB_living_bets.md",
      "META.md",
    ];
    for (const path of expected) {
      assert.ok(
        manifest.new_l0.bundle_files.some((f) => f.path === path),
        `${path} must be in the bundle`,
      );
    }
  });
});
