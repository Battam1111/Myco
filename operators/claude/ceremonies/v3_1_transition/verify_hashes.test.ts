// Verify the v3.1 transition manifest reproduces from the current bundle.
//
// This test is a CI gate:
//   - PASS = `manifest.json` matches the current `docs/architecture/L0/`
//     bundle bit-for-bit (every file's SHA-256 + the bundle BLAKE3).
//   - FAIL = either someone modified an L0 file without re-running
//     `compute_hashes.ts` (drift), OR `compute_hashes.ts` itself broke
//     (canonical-bytes regression — L1/HARD_RULES C18 territory).
//
// When the cultivator intentionally amends L0 doctrine, they MUST:
//   1. Run a new ceremony to mint a fresh `l0_revision_attested:{prefix}`
//      DAG event signed by the owner key (per M-anchor-5 §9.2.4).
//   2. Regenerate `manifest.json` so this test goes green again.
//
// Skipping step 1 = silent doctrine drift = the substrate observatory
// (production-side) would detect the on-chain v3.1 attestation no longer
// matches the live bundle hash. This test catches it pre-commit.

import { describe, it } from "node:test";
import { strict as assert } from "node:assert";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

import {
  computeNewL0Hash,
  computePriorL0Hash,
  DIFF_SUMMARY,
  PRIOR_L0_COMMIT,
  PRIOR_L0_PATH,
} from "./compute_hashes.ts";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

interface Manifest {
  schema_version: number;
  ceremony: string;
  prior_l0: {
    commit: string;
    path: string;
    byte_length: number;
    sha256_hex: string;
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

describe("v3.1-stratigraphy transition — hash manifest reproducibility", () => {
  const manifest = loadManifest();

  it("manifest.schema_version is 1 (no breaking change since seal)", () => {
    assert.equal(manifest.schema_version, 1);
  });

  it("manifest.ceremony name is locked", () => {
    assert.equal(manifest.ceremony, "v3.1-stratigraphy-transition");
  });

  it("manifest.diff_summary matches compute_hashes.DIFF_SUMMARY constant", () => {
    // If these drift, the signed envelope canonical-bytes would change,
    // invalidating any prior signature. Bumping diff_summary requires a
    // new ceremony.
    assert.equal(manifest.diff_summary, DIFF_SUMMARY);
  });

  it("manifest.prior_l0 fields match the pinned commit + path", () => {
    assert.equal(manifest.prior_l0.commit, PRIOR_L0_COMMIT);
    assert.equal(manifest.prior_l0.path, PRIOR_L0_PATH);
  });

  it("prior_l0_hash reproduces from git show e796451:L0_VISION.md", () => {
    const computed = computePriorL0Hash();
    assert.equal(
      computed.byteLength,
      manifest.prior_l0.byte_length,
      `prior L0 byte length drifted: manifest=${manifest.prior_l0.byte_length} computed=${computed.byteLength}`,
    );
    assert.equal(
      computed.hashHex,
      manifest.prior_l0.sha256_hex,
      `prior_l0_hash drift: manifest=${manifest.prior_l0.sha256_hex} computed=${computed.hashHex}`,
    );
  });

  it("new_l0_hash reproduces from current docs/architecture/L0/ bundle", () => {
    const computed = computeNewL0Hash();
    assert.equal(
      computed.canonicalBytesLength,
      manifest.new_l0.canonical_bytes_length,
      `canonical bytes length drift: manifest=${manifest.new_l0.canonical_bytes_length} ` +
        `computed=${computed.canonicalBytesLength} — an L0 file was modified after manifest was sealed`,
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
});
