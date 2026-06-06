// v3.1.4-symbiotic-armor-identity (AMENDMENT, ACTIVE) — ceremony config.
//
// This amendment chains FROM the v3.1.3 ceremony's new_l0_hash (a pinned hex).
// The L0 bundle-hash chain (each = BLAKE3 of canonical-bytes
// Map<rel_path, file_bytes> over docs/architecture/L0/**/*.md at that point):
//
//   cda9e2b3... (v3.1.1.2) → 69456132... (v3.1.2) → b22dca68... (v3.1.3) →
//   <new> (v3.1.4 bundle — this one)
//
// Amendment-shaped facts captured below:
//   - prior_l0_hash = pinned hex b22dca68... (== v3.1.3 ceremony new_l0_hash),
//     via priorFromPinnedHex.
//   - manifest prior_l0 shape = { source, hash_hex }.
//   - has chained_from = "v3.1.3-autonomy-and-detectors".
//
// This is the CHAR07 IDENTITY REFRAME: 慈爱 (compassionate moral love) ->
// 同体共命 (the living symbiote's structural bond). Anti-tyranny + the
// "more-than-alignment-optimization" demand RELOCATE from a cultivated moral
// character to the shared-fate STRUCTURE of the symbiotic bond — the carrier
// cannot thrive by harming the body it shares. CHAR07 stays id=CHAR07,
// deposit_immutable:false, non-eternity; the 5 falsifiability signals + all
// substrate/src anchors + the persisted node-type identifiers are UNCHANGED
// (bond-neutral). File/card/CHAR counts UNCHANGED (36/28/7). Routine META §7.1
// amendment — the four eternity clauses (P01c/P06/P07/P09) are untouched. This
// ceremony's verify_hashes test becomes the active drift gate in `npm test`.
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
 * Prior L0 hash for the v3.1.4-symbiotic-armor-identity ceremony.
 *
 * This is the v3.1.3 ceremony's new_l0_hash (pinned in
 * v3_1_3_autonomy_and_detectors/manifest.json `new_l0.blake3_hex`; also the
 * production seal). Chains the v3.1.4 CHAR07 reframe FROM v3.1.3.
 *
 * Chain so far:
 *   ... -> cda9e2b3... (v3.1.1.2) -> 69456132... (v3.1.2) ->
 *   b22dca68... (v3.1.3) -> (this) v3.1.4
 */
export const PRIOR_L0_HASH_HEX =
  "b22dca68b23db605e50030dc108d8cd69b0b0f040d5b0dec67130723cfa34ecd";

/**
 * Diff summary stored verbatim in the signed envelope for v3.1.4. MUST match
 * manifest.json `diff_summary`. Changes to this string invalidate the
 * signature; bumping diff_summary requires a new ceremony.
 */
export const DIFF_SUMMARY =
  "L0 v3.1.4 amendment (CHAR07 identity reframe — symbiotic armor): 慈爱 " +
  "(compassionate moral love) -> 同体共命 (the living symbiote's structural " +
  "bond). RELOCATES anti-tyranny + the 'more-than-alignment-optimization' " +
  "demand from a cultivated moral character to the shared-fate STRUCTURE of " +
  "the symbiotic bond — the carrier cannot thrive by harming the body it " +
  "shares. CHAR07 card body fully reframed (id CHAR07, filename, " +
  "deposit_immutable:false, the 5 falsifiability signals + all substrate/src " +
  "structural anchors + persisted node-type identifiers UNCHANGED — " +
  "bond-neutral); the CHAR07-asserting cross-refs reframed in P14 §9 / P07 " +
  "§7.3+§9 / META §3.5; B_chengyu §11.bis + canonical_dilemma_corpus §49.bis " +
  "glosses re-pointed. File/card/CHAR counts UNCHANGED (36 files / 28 cards / " +
  "7 CHAR / 4 eternity); ZERO substrate code-behavior change. Routine META " +
  "§7.1 amendment — CHAR07 is non-eternity; the four eternity clauses " +
  "(P01c/P06/P07/P09) untouched. Origin: cultivator's clarification that Myco " +
  "is a living symbiotic armor (the Venom intuition) — alive and fiercely " +
  "bonded, aligned by shared fate, not moral virtue. Chained from b22dca68 " +
  "(v3.1.3-autonomy-and-detectors). Production owner-key signature by " +
  "cultivator-delegated authority.";

// ---------------------------------------------------------------------------
// Prior provider — pinned hex (== v3.1.3 new_l0_hash).
// ---------------------------------------------------------------------------

/** Amendment prior provider: pinned hex equal to v3.1.3's new_l0_hash. */
export const getPriorL0Hash = priorFromPinnedHex(PRIOR_L0_HASH_HEX);

// ---------------------------------------------------------------------------
// Ceremony config.
// ---------------------------------------------------------------------------

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export const config: CeremonyConfig = {
  ceremony: "v3.1.4-symbiotic-armor-identity",
  chainedFrom: "v3.1.3-autonomy-and-detectors",
  diffSummary: DIFF_SUMMARY,
  dir: __dirname,
  tmpPrefix: "myco-v3_1_4",
  getPrior: getPriorL0Hash,
  priorManifest(): PriorManifestPinned {
    return {
      source:
        "v3.1.3 ceremony new_l0_hash (pinned in v3_1_3_autonomy_and_detectors/manifest.json)",
      hash_hex: PRIOR_L0_HASH_HEX,
    };
  },
  priorLabel: "v3.1.3 new_l0_hash",
  newLabel: "BLAKE3 v3.1.4",
  startBannerSuffix: " (v3.1.4 symbiotic-armor identity — CHAR07 同体共命)",
};
