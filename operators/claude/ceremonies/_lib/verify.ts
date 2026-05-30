// Shared verify_hashes.test.ts assertions for L0-revision ceremonies.
//
// Kept separate from ceremony.ts so the run_ceremony / compute_hashes CLI
// import graph never pulls in `node:test`. Each ceremony's verify_hashes.test
// imports `loadManifest` + `verifyManifest` from here, passes its own config,
// then adds its per-ceremony extra `describe`/`it` blocks verbatim.
//
// Per L1/HARD_RULES C18 canonical_bytes_render_drift (CRITICAL).

import { describe, it } from "node:test";
import { strict as assert } from "node:assert";
import { readFileSync } from "node:fs";
import { join } from "node:path";

import { computeNewL0Hash, type BundleFileDigest } from "./bundle_hash.ts";
import { type CeremonyConfig } from "./ceremony.ts";

/** Shape of a ceremony manifest as loaded by the verify test. */
export interface CeremonyManifest {
  schema_version: number;
  ceremony: string;
  chained_from?: string;
  prior_l0: Record<string, unknown>;
  new_l0: {
    root: string;
    bundle_files: BundleFileDigest[];
    canonical_bytes_length: number;
    blake3_hex: string;
  };
  diff_summary: string;
}

/** Load a ceremony's manifest.json from its directory. */
export function loadManifest(dir: string): CeremonyManifest {
  const path = join(dir, "manifest.json");
  return JSON.parse(readFileSync(path, "utf-8")) as CeremonyManifest;
}

/**
 * The assertions shared by every ceremony's verify_hashes test. Registers a
 * `describe(...)` block of `it(...)` cases. Per-ceremony extras (CHAR07
 * present, P07 byte-distinct, P03 byte-expanded, genesis prior commit/path,
 * etc.) stay in each ceremony's own test file alongside a call to this.
 *
 * The manifest is loaded by the caller from cfg.dir (via loadManifest). The
 * expected ceremony name + chained_from + diff_summary + prior hash all come
 * from cfg, so this single function covers genesis and amendments.
 */
export function verifyManifest(cfg: CeremonyConfig, manifest: CeremonyManifest): void {
  describe(`${cfg.ceremony} — hash manifest reproducibility (shared)`, () => {
    it("manifest.schema_version is 1 (no breaking change since seal)", () => {
      assert.equal(manifest.schema_version, 1);
    });

    it("manifest.ceremony name is locked", () => {
      assert.equal(manifest.ceremony, cfg.ceremony);
    });

    if (cfg.chainedFrom !== null) {
      it("manifest.chained_from points at the prior ceremony", () => {
        assert.equal(manifest.chained_from, cfg.chainedFrom);
      });
    }

    it("manifest.diff_summary matches the ceremony DIFF_SUMMARY constant", () => {
      // If these drift, the signed envelope canonical-bytes would change,
      // invalidating any prior signature. Bumping diff_summary requires a new
      // ceremony.
      assert.equal(manifest.diff_summary, cfg.diffSummary);
    });

    it("prior_l0_hash matches the ceremony's prior provider", () => {
      const computed = cfg.getPrior();
      // The manifest stores the prior hash under sha256_hex (genesis) or
      // hash_hex (amendment); whichever is present must equal the provider.
      const manifestHex =
        (manifest.prior_l0 as { sha256_hex?: string }).sha256_hex ??
        (manifest.prior_l0 as { hash_hex?: string }).hash_hex;
      assert.equal(
        manifestHex,
        computed.hashHex,
        `prior_l0_hash drift: manifest=${manifestHex} computed=${computed.hashHex}`,
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
}
