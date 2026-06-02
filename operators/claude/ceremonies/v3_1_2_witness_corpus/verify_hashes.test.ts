// Verify the v3.1.2-witness-corpus ceremony manifest reproduces from the
// current bundle.
//
// CI gate (THIS is the active drift gate registered in `npm test`):
//   - PASS = `manifest.json` matches the current `docs/architecture/L0/`
//     bundle (every file's SHA-256 + the bundle BLAKE3).
//   - FAIL = either someone modified an L0 file without re-running
//     `compute_hashes.ts` (drift), OR `compute_hashes.ts` itself broke
//     (canonical-bytes regression — L1/HARD_RULES C18 territory).
//
// The shared assertions live in ../_lib/verify.ts::verifyManifest; this file
// adds the v3.1.2-specific extras (the Layer C witness-corpus milestone: 36
// files unchanged, META expanded by the §5 kind: amendment, P07 + CHAR07 byte-
// distinct from v3.1.1.2 after the witness re-pointing + stale-marker scrubs).
//
// The chained chain is:
//   v3.1 → v3.1.1 (mortality refinement + 慈爱) → v3.1.1.1 (P03 §3.3 reframe)
//   → v3.1.1.2 (stale-fact correction) → v3.1.2 (Layer C witness corpus)
// The v3.1 / v3.1.1 / v3.1.1.1 / v3.1.1.2 ceremonies' verify tests are NOT
// registered in npm test (they fail by design after each subsequent amendment);
// v3.1.2's is active.

import { describe, it } from "node:test";
import { strict as assert } from "node:assert";

import { loadManifest, verifyManifest } from "../_lib/verify.ts";
import { config } from "./config.ts";

const manifest = loadManifest(config.dir);

// Shared assertions (schema_version, ceremony name, chained_from, diff_summary,
// prior-hash chain link, new_l0_hash, per-file SHA-256).
verifyManifest(config, manifest);

// v3.1.2-specific extras (the witness-corpus milestone).
describe("v3.1.2-witness-corpus — amendment-specific checks", () => {
  it("bundle is still exactly 36 files (witness re-pointing added no L0 files)", () => {
    // The witness corpus re-points existing cards + references EXISTING inline
    // dilemmas in canonical_dilemma_corpus/INDEX.md; it does NOT promote any
    // dilemma to a standalone D-*.md file, so the file count is unchanged.
    assert.equal(
      manifest.new_l0.bundle_files.length,
      36,
      `expected 36 bundle files; got ${manifest.new_l0.bundle_files.length}`,
    );
  });

  it("META.md expanded past v3.1.1.2 (the §5 kind: + shipped-milestone amendment)", () => {
    // v3.1.1.2 META was 42283 bytes; the v3.1.2 §3.1/§5.2/§5.5/§5.6 amendment
    // (kind: discriminator + executable/narrative split + C67 + SHIPPED notes)
    // only adds prose.
    const meta = manifest.new_l0.bundle_files.find((f) => f.path === "META.md");
    assert.ok(meta, "META.md must be in bundle");
    assert.ok(
      meta.byte_length > 42283,
      `v3.1.2 META should be larger than v3.1.1.2's 42283 (got ${meta.byte_length})`,
    );
  });

  it("P07_mortality.md is byte-distinct from v3.1.1.2 (witness re-point + §12-14 scrub)", () => {
    // v3.1.1.2 P07 was 30364 bytes; v3.1.2 re-points its witnesses + scrubs the
    // "NEW / to be added in v3.1.1 cascade" markers to shipped reality. It stays
    // substantially larger than v3.1's small P07.
    const p07 = manifest.new_l0.bundle_files.find(
      (f) => f.path === "cards/P07_mortality.md",
    );
    assert.ok(p07, "P07_mortality.md must be in bundle");
    assert.ok(
      p07.byte_length > 15000 && p07.byte_length !== 30364,
      `v3.1.2 P07 should be >15000 and byte-distinct from v3.1.1.2's 30364 (got ${p07.byte_length})`,
    );
  });

  it("CHAR07_caring.md is byte-distinct from v3.1.1.2 (front-matter arrays + §13-15 scrub)", () => {
    // v3.1.1.2 CHAR07 was 24099 bytes; v3.1.2 populates its chengyu_fragments +
    // canonical_dilemmas front-matter (were []) + real §13 anchors + scrubs
    // §14/§15 "to be added".
    const char07 = manifest.new_l0.bundle_files.find(
      (f) => f.path === "cards/CHAR07_caring.md",
    );
    assert.ok(char07, "CHAR07_caring.md must be in bundle");
    assert.ok(
      char07.byte_length !== 24099,
      `v3.1.2 CHAR07 should be byte-distinct from v3.1.1.2's 24099 (got ${char07.byte_length})`,
    );
  });
});
