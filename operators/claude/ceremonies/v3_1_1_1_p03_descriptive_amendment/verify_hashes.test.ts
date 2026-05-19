// Verify the v3.1.1.1 P03-descriptive-amendment ceremony manifest reproduces
// from the current bundle.
//
// CI gate:
//   - PASS = `manifest.json` matches the current `docs/architecture/L0/`
//     bundle (every file's SHA-256 + the bundle BLAKE3).
//   - FAIL = either someone modified an L0 file without re-running
//     `compute_hashes.ts` (drift), OR `compute_hashes.ts` itself broke
//     (canonical-bytes regression — L1/HARD_RULES C18 territory).
//
// Note: this is the v3.1.1.1 descriptive amendment. The chained chain is:
//   v3.1 → v3.1.1 (mortality refinement + 慈爱) → v3.1.1.1 (P03 §3.3 reframe)
// The v3.1 and v3.1.1 ceremonies' verify_hashes tests are NOT registered in
// npm test (they would fail by design after each subsequent amendment);
// v3.1.1.1's is the active drift gate.

import { describe, it } from "node:test";
import { strict as assert } from "node:assert";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  computeNewL0Hash,
  getPriorL0Hash,
  DIFF_SUMMARY,
  PRIOR_L0_HASH_HEX,
} from "./compute_hashes.ts";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

interface Manifest {
  schema_version: number;
  ceremony: string;
  chained_from: string;
  prior_l0: {
    source: string;
    hash_hex: string;
  };
  new_l0: {
    root: string;
    bundle_files: { path: string; byte_length: number; sha256_hex: string }[];
    canonical_bytes_length: number;
    blake3_hex: string;
  };
  diff_summary: string;
}

function loadManifest(): Manifest {
  const path = join(__dirname, "manifest.json");
  return JSON.parse(readFileSync(path, "utf-8")) as Manifest;
}

describe("v3.1.1.1-p03-descriptive-amendment — hash manifest reproducibility", () => {
  const manifest = loadManifest();

  it("manifest.schema_version is 1 (no breaking change since seal)", () => {
    assert.equal(manifest.schema_version, 1);
  });

  it("manifest.ceremony name is locked", () => {
    assert.equal(manifest.ceremony, "v3.1.1.1-p03-descriptive-amendment");
  });

  it("manifest.chained_from points at the v3.1.1 ceremony", () => {
    assert.equal(manifest.chained_from, "v3.1.1-mortality-refinement-and-charite");
  });

  it("manifest.diff_summary matches compute_hashes.DIFF_SUMMARY constant", () => {
    assert.equal(manifest.diff_summary, DIFF_SUMMARY);
  });

  it("manifest.prior_l0.hash_hex matches the v3.1.1 new_l0_hash (chain link)", () => {
    assert.equal(manifest.prior_l0.hash_hex, PRIOR_L0_HASH_HEX);
    const computed = getPriorL0Hash();
    assert.equal(computed.hashHex, manifest.prior_l0.hash_hex);
  });

  it("new_l0_hash reproduces from current docs/architecture/L0/ bundle", () => {
    const computed = computeNewL0Hash();
    assert.equal(
      computed.canonicalBytesLength,
      manifest.new_l0.canonical_bytes_length,
      `canonical bytes length drift: manifest=${manifest.new_l0.canonical_bytes_length} ` +
        `computed=${computed.canonicalBytesLength} — an L0 file was modified after v3.1.1 manifest was sealed`,
    );
    assert.equal(
      computed.hashHex,
      manifest.new_l0.blake3_hex,
      `new_l0_hash drift: manifest=${manifest.new_l0.blake3_hex} computed=${computed.hashHex} — ` +
        `re-run compute_hashes.ts and re-sign the ceremony, or revert the L0 change`,
    );
  });

  it("every bundle file's per-file SHA-256 is byte-stable", () => {
    const computed = computeNewL0Hash();
    assert.equal(
      computed.bundleFiles.length,
      manifest.new_l0.bundle_files.length,
      `bundle file count drift: manifest=${manifest.new_l0.bundle_files.length} ` +
        `computed=${computed.bundleFiles.length} — a file was added or removed`,
    );
    for (let i = 0; i < computed.bundleFiles.length; i++) {
      const a = computed.bundleFiles[i]!;
      const b = manifest.new_l0.bundle_files[i]!;
      assert.equal(a.path, b.path, `bundle file order drift at index ${i}`);
      assert.equal(
        a.byte_length,
        b.byte_length,
        `bundle file ${a.path} byte length drift`,
      );
      assert.equal(
        a.sha256_hex,
        b.sha256_hex,
        `bundle file ${a.path} SHA-256 drift`,
      );
    }
  });

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
      `v3.1.1+ P07 should be substantially larger than v3.1 (got ${p07.byte_length} bytes)`,
    );
  });

  it("P03_resumable_evolution.md is byte-expanded from v3.1.1 (Sprint 6.D §10.4 addition)", () => {
    // Sprint 6.D added §10.4 acknowledged-debt section (~3500 bytes) +
    // reframed §3.3 / §4.3 / §5.2 / §7.1 / §12. v3.1.1 P03 was 12127 bytes;
    // v3.1.1.1 should be >14000 bytes.
    const p03 = manifest.new_l0.bundle_files.find(
      (f) => f.path === "cards/P03_resumable_evolution.md",
    );
    assert.ok(p03, "P03_resumable_evolution.md must be in bundle");
    assert.ok(
      p03.byte_length > 14000,
      `v3.1.1.1 P03 should be substantially larger than v3.1.1's 12127 ` +
        `(Sprint 6.D §10.4 addition); got ${p03.byte_length} bytes`,
    );
  });
});
