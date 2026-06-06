// Verify the v3.1.4-symbiotic-armor-identity ceremony manifest reproduces from
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
// adds the v3.1.4-specific extras (the CHAR07 reframe: still 36 files, the
// reframed CHAR07 card + its cross-ref carriers all present).
//
// The chained chain is:
//   v3.1 -> v3.1.1 -> v3.1.1.1 -> v3.1.1.2 -> v3.1.2 -> v3.1.3
//   -> v3.1.4 (CHAR07 同体共命 — symbiotic-armor identity reframe)
// The earlier ceremonies' verify tests are NOT registered in npm test (they
// fail by design after each subsequent amendment); v3.1.4's is active.

import { describe, it } from "node:test";
import { strict as assert } from "node:assert";

import { loadManifest, verifyManifest } from "../_lib/verify.ts";
import { config } from "./config.ts";

const manifest = loadManifest(config.dir);

// Shared assertions (schema_version, ceremony name, chained_from, diff_summary,
// prior-hash chain link, new_l0_hash, per-file SHA-256).
verifyManifest(config, manifest);

// v3.1.4-specific extras (the CHAR07 identity reframe).
describe("v3.1.4-symbiotic-armor-identity — amendment-specific checks", () => {
  it("bundle is still exactly 36 files (the CHAR07 reframe adds/removes no L0 files)", () => {
    // REFRAME-in-place: CHAR07 keeps its id, filename, and slot — no card added
    // or deleted, so the file count is invariant across the reseal.
    assert.equal(
      manifest.new_l0.bundle_files.length,
      36,
      `expected 36 bundle files; got ${manifest.new_l0.bundle_files.length}`,
    );
  });

  it("the reframed CHAR07 card + its cross-ref carriers are present in the bundle", () => {
    // The reframe rewrote cards/CHAR07_caring.md (同体共命) and re-pointed the
    // CHAR07-asserting cross-refs in these files; their new per-file SHA-256 is
    // checked by verifyManifest above. Sanity-check they are all still sealed.
    const expected = [
      "cards/CHAR07_caring.md",
      "cards/P14_telos.md",
      "cards/P07_mortality.md",
      "META.md",
      "B_chengyu.md",
      "canonical_dilemma_corpus/INDEX.md",
    ];
    for (const path of expected) {
      assert.ok(
        manifest.new_l0.bundle_files.some((f) => f.path === path),
        `${path} must be in the bundle`,
      );
    }
  });
});
