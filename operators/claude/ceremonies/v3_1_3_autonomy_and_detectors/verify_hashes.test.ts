// Verify the v3.1.3-autonomy-and-detectors ceremony manifest reproduces from
// the current bundle.
//
// CI gate (THIS is the active drift gate registered in `npm test`):
//   - PASS = `manifest.json` matches the current `docs/architecture/L0/`
//     bundle (every file's SHA-256 + the bundle BLAKE3).
//   - FAIL = either someone modified an L0 file without re-running
//     `compute_hashes.ts` (drift), OR `compute_hashes.ts` itself broke
//     (canonical-bytes regression — L1/HARD_RULES C18 territory).
//
// The shared assertions live in ../_lib/verify.ts::verifyManifest; this file
// adds the v3.1.3-specific extras (Phase ①②③: 36 files unchanged, META
// expanded by the §5.5 run-and-verify amendment, the 8 re-pointed-witness cards
// all present).
//
// The chained chain is:
//   v3.1 → v3.1.1 → v3.1.1.1 → v3.1.1.2 → v3.1.2 (Layer C witness corpus)
//   → v3.1.3 (autonomy + detectors + witness maturity)
// The earlier ceremonies' verify tests are NOT registered in npm test (they
// fail by design after each subsequent amendment); v3.1.3's is active.

import { describe, it } from "node:test";
import { strict as assert } from "node:assert";

import { loadManifest, verifyManifest } from "../_lib/verify.ts";
import { config } from "./config.ts";

const manifest = loadManifest(config.dir);

// Shared assertions (schema_version, ceremony name, chained_from, diff_summary,
// prior-hash chain link, new_l0_hash, per-file SHA-256).
verifyManifest(config, manifest);

// v3.1.3-specific extras (the Phase ①②③ amendment).
describe("v3.1.3-autonomy-and-detectors — amendment-specific checks", () => {
  it("bundle is still exactly 36 files (descriptive amendment added no L0 files)", () => {
    // The reseal re-points witnesses + updates debt-status prose; it adds no
    // new L0 .md files (no new dilemma/catechumenate files).
    assert.equal(
      manifest.new_l0.bundle_files.length,
      36,
      `expected 36 bundle files; got ${manifest.new_l0.bundle_files.length}`,
    );
  });

  it("META.md grew (the §5.2/§5.5/§5.6 run-and-verify amendment is prose-only)", () => {
    // v3.1.2 META was already > 42283 bytes; the v3.1.3 §5 run-and-verify-LIVE
    // amendment only adds prose, so META stays above that floor.
    const meta = manifest.new_l0.bundle_files.find((f) => f.path === "META.md");
    assert.ok(meta, "META.md must be in bundle");
    assert.ok(
      meta.byte_length > 42283,
      `v3.1.3 META should exceed 42283 bytes (got ${meta.byte_length})`,
    );
  });

  it("all 8 re-pointed-witness cards are present in the bundle", () => {
    // Phase ③ replaced the ~7 nearest-available witness slots across these cards
    // with exact-polarity tests; the reseal re-pointed them. Sanity-check they
    // are all in the sealed bundle (the per-file SHA-256 is checked by
    // verifyManifest above).
    const expected = [
      "cards/P02_eternal_ingestion.md",
      "cards/P04_eternal_iteration.md",
      "cards/P05_universal_interconnection.md",
      "cards/P07_mortality.md",
      "cards/P14_telos.md",
      "cards/P01c_asymmetric_carrier.md",
      "cards/LB_living_bets.md",
      "cards/COV01_fiduciary_duty.md",
    ];
    for (const path of expected) {
      assert.ok(
        manifest.new_l0.bundle_files.some((f) => f.path === path),
        `${path} must be in the bundle`,
      );
    }
  });
});
