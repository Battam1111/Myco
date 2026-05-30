// v3.1.1-mortality-refinement-and-charite (AMENDMENT) — ceremony configuration.
//
// This amendment chains FROM the v3.1 transition's new_l0_hash (a pinned hex),
// not from the original e796451 DRAFT 9 SHA-256. Chain so far:
//
//   e796451 (DRAFT 9) → 5eacf3e7... (v3.1 attestation) → b1bec59a... (v3.1.1)
//
// Amendment-shaped facts captured below:
//   - prior_l0_hash = pinned hex b1bec59a... (== v3.1 ceremony new_l0_hash),
//     via priorFromPinnedHex.
//   - manifest prior_l0 shape = { source, hash_hex }.
//   - has chained_from = "v3.1-stratigraphy-transition".
//
// Everything else is the shared _lib machinery.
//
// Per L1/HARD_RULES C18 canonical_bytes_render_drift (CRITICAL).

import { dirname } from "node:path";
import { fileURLToPath } from "node:url";

import { priorFromPinnedHex } from "../_lib/bundle_hash.ts";
import {
  type CeremonyConfig,
  type PriorManifestPinned,
} from "../_lib/ceremony.ts";

// ---------------------------------------------------------------------------
// Constants — pinned forever.
// ---------------------------------------------------------------------------

/**
 * Prior L0 hash for the v3.1.1 amendment ceremony.
 *
 * This is the v3.1 ceremony's new_l0_hash (computed by v3_1_transition and
 * pinned in v3_1_transition/manifest.json). Chains the v3.1.1 amendment FROM
 * the v3.1 transition.
 */
export const PRIOR_L0_HASH_HEX =
  "b1bec59acc8c5061020640a265a9772e734604425b6eda4b5da1759f9987c699";

/**
 * Diff summary stored verbatim in the signed envelope for v3.1.1. MUST match
 * manifest.json `diff_summary`. Changes to this string invalidate the
 * signature; bumping diff_summary requires a new ceremony.
 *
 * VERBATIM — byte-for-byte identical to the original compute_hashes.ts.
 */
export const DIFF_SUMMARY =
  "L0 v3.1.1 amendment (mortality refinement + 慈爱 introduction): " +
  "(1) P07 reinterpreted — primary subject is mandatory internal mortality (必朽) " +
  "of 应朽 family parts; canonical exemplars 过时/错误/冗余/无用 are illustrative " +
  "not exhaustive (包括但不限于); L1 authorized to recognize additional family " +
  "members (有害/矛盾/僵化/异化/污染/失效/寄生/滞塞/死症/...). Whole-substrate " +
  "eventual rest preserved as downstream boundary. Slogan 能朽 → 必朽. " +
  "(2) CHAR07 慈爱 added as developmental anti-tyranny character (developmental, " +
  "non-eternity); sister to P07 (P7 prevents bloat-death, CHAR07 prevents " +
  "tyrant-becoming). Origin: cultivator's correction 'capability growth toward " +
  "godhood is permitted; tyranny is not; the structural protection is character-" +
  "level care, not lifespan limitation' (神爱世人 framing). " +
  "(3) Cascading updates to COV04 (敬其能朽 → 敬其必朽 + internal-mortality " +
  "honoring), CHAR03 (extended to both senses), P02/P03/P04/P14 (P07/CHAR07 " +
  "interlock rows), META (eternity-clause inventory wording refinement), " +
  "PROVENANCE (v3.1.1 amendment record), B_chengyu (B051-B060 metabolism + " +
  "love fragments), canonical_dilemma_corpus (D-0050..D-0054), " +
  "L1/CONTINUITY (prune-phase added to deep cycle), L1/HARD_RULES " +
  "(C54/C55/C56 anticipated + F24 anticipated), L2/OBSERVABILITY (new metrics). " +
  "Sealed 2026-05-19.";

// ---------------------------------------------------------------------------
// Prior provider — pinned hex (== v3.1 new_l0_hash).
// ---------------------------------------------------------------------------

/** Amendment prior provider: pinned hex equal to v3.1's new_l0_hash. */
export const getPriorL0Hash = priorFromPinnedHex(PRIOR_L0_HASH_HEX);

// ---------------------------------------------------------------------------
// Ceremony config.
// ---------------------------------------------------------------------------

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export const config: CeremonyConfig = {
  ceremony: "v3.1.1-mortality-refinement-and-charite",
  chainedFrom: "v3.1-stratigraphy-transition",
  diffSummary: DIFF_SUMMARY,
  dir: __dirname,
  tmpPrefix: "myco-v3_1_1",
  getPrior: getPriorL0Hash,
  priorManifest(): PriorManifestPinned {
    return {
      source:
        "v3.1 ceremony new_l0_hash (pinned in v3_1_transition/manifest.json)",
      hash_hex: PRIOR_L0_HASH_HEX,
    };
  },
  priorLabel: "v3.1 new_l0_hash",
  newLabel: "BLAKE3 v3.1.1",
  startBannerSuffix: " (v3.1.1 amendment)",
};
