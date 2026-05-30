// v3.1-stratigraphy transition (GENESIS) — ceremony configuration.
//
// The genesis ceremony differs from the amendments in exactly these ways,
// all captured below:
//   - prior_l0_hash = SHA-256 of `git show e796451:docs/architecture/L0_VISION.md`
//     (the DRAFT 9 SEALED monolith), via priorFromGitSha256 — NOT a pinned hex.
//   - manifest prior_l0 shape = { commit, path, byte_length, sha256_hex }.
//   - NO chained_from (chainedFrom: null) — this is the chain origin.
//   - its CeremonyResult therefore omits ceremony/chained_from (the runner
//     drops them when chainedFrom === null).
//
// Everything else (the bundle walk, computeNewL0Hash, the signing flow) is the
// shared _lib machinery.
//
// Per L0/cards/AS_anchor_surface §3.4 + M-anchor-5 §9.2.4.

import { dirname } from "node:path";
import { fileURLToPath } from "node:url";

import {
  priorFromGitSha256,
  type PriorL0Hash,
} from "../_lib/bundle_hash.ts";
import {
  type CeremonyConfig,
  type PriorManifestGit,
} from "../_lib/ceremony.ts";

// ---------------------------------------------------------------------------
// Constants — pinned forever.
// ---------------------------------------------------------------------------

/** Commit hash of the prior monolithic L0 (DRAFT 9 SEALED, 2026-05-17). */
export const PRIOR_L0_COMMIT = "e796451";

/** Path-in-prior-commit of the monolithic L0 file. */
export const PRIOR_L0_PATH = "docs/architecture/L0_VISION.md";

/**
 * Diff summary stored verbatim in the signed envelope. Must match
 * manifest.json `diff_summary`. Changes to this string invalidate the
 * signature; bumping diff_summary requires a new ceremony.
 *
 * VERBATIM — byte-for-byte identical to the original compute_hashes.ts.
 */
export const DIFF_SUMMARY =
  "L0 v3.1-stratigraphy: DRAFT 9 SEALED monolith → 4-layer doctrine institution " +
  "(Layer A 27 cards + Layer B 50 chengyu + Layer C 49 canonical dilemmas + " +
  "Layer D catechumenate placeholder + META + PROVENANCE). 4 eternity-clause " +
  "cards (P01c, P06, P07, P09). Phase 1+2 11-stream research + 3 craft rounds " +
  "+ Phase 3 unknown-unknown hunt with 7 amendments. Sealed 2026-05-18.";

// ---------------------------------------------------------------------------
// Prior provider — SHA-256 of the git-history monolith.
// ---------------------------------------------------------------------------

const priorProvider = priorFromGitSha256(PRIOR_L0_COMMIT, PRIOR_L0_PATH);

/** Genesis prior provider (also surfaces byteLength for the manifest). */
export function getPriorL0Hash(): PriorL0Hash & { byteLength: number } {
  return priorProvider();
}

// ---------------------------------------------------------------------------
// Ceremony config.
// ---------------------------------------------------------------------------

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export const config: CeremonyConfig = {
  ceremony: "v3.1-stratigraphy-transition",
  chainedFrom: null, // GENESIS — chain origin, no prior ceremony.
  diffSummary: DIFF_SUMMARY,
  dir: __dirname,
  tmpPrefix: "myco-v3_1",
  getPrior: getPriorL0Hash,
  priorManifest(): PriorManifestGit {
    const prior = getPriorL0Hash();
    return {
      commit: PRIOR_L0_COMMIT,
      path: PRIOR_L0_PATH,
      byte_length: prior.byteLength,
      sha256_hex: prior.hashHex,
    };
  },
  priorLabel: "SHA-256 @ e796451",
  newLabel: "BLAKE3 v3.1",
  startBannerSuffix: "",
};
