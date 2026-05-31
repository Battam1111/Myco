// v3.1.1.2-descriptive-amendment (AMENDMENT, ACTIVE) — ceremony config.
//
// This amendment chains FROM the v3.1.1.1 ceremony's new_l0_hash (a pinned hex).
// The L0 bundle-hash chain (each = BLAKE3 of canonical-bytes
// Map<rel_path, file_bytes> over docs/architecture/L0/**/*.md at that point):
//
//   b1bec59a... (v3.1 bundle) → 798c047d... (v3.1.1 bundle) →
//   7267dc58... (v3.1.1.1 bundle) → <new> (v3.1.1.2 bundle — this one)
//
// Amendment-shaped facts captured below:
//   - prior_l0_hash = pinned hex 7267dc58... (== v3.1.1.1 ceremony new_l0_hash),
//     via priorFromPinnedHex.
//   - manifest prior_l0 shape = { source, hash_hex }.
//   - has chained_from = "v3.1.1.1-p03-descriptive-amendment".
//
// This ceremony's verify_hashes test is the one registered in `npm test`
// (the active drift gate). Everything else is the shared _lib machinery.
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
 * Prior L0 hash for the v3.1.1.2 descriptive-amendment ceremony.
 *
 * This is the v3.1.1.1 ceremony's new_l0_hash (pinned in
 * v3_1_1_1_p03_descriptive_amendment/manifest.json). Chains the v3.1.1.2
 * descriptive amendment (stale-fact correction to shipped reality) FROM the
 * v3.1.1.1 P03-descriptive amendment.
 *
 * Chain so far:
 *   e796451 (DRAFT 9) → 5eacf3e7... (v3.1) → b1bec59a... (v3.1) →
 *   798c047d... (v3.1.1) → 7267dc58... (v3.1.1.1) → (this) v3.1.1.2
 */
export const PRIOR_L0_HASH_HEX =
  "7267dc58aa81d3dcd7ef08c3f83d49b0b0ab9b910f72a7a51c92d181c7eae4ba";

/**
 * Diff summary stored verbatim in the signed envelope for v3.1.1.2. MUST match
 * manifest.json `diff_summary`. Changes to this string invalidate the
 * signature; bumping diff_summary requires a new ceremony.
 */
export const DIFF_SUMMARY =
  "L0 v3.1.1.2 descriptive amendment (Task #8j): corrects stale descriptive " +
  "facts to match shipped reality. (1) README/PROVENANCE file & artifact " +
  "counts: 32→36 files, 26→28 cards, 12→13 P-cards, 6→7 Character cards " +
  "(CHAR07 added to tree), 50→60 B-chengyu fragments, 49→54 canonical " +
  "dilemmas, catechumenate tree updated (INDEX+TEMPLATE+HOW_TO_ADD_A_SESSION). " +
  "(2) P03 §10.4: multi-cycle two-phase migration shipped as opt-in MVP " +
  "(commit 8d6a647, kernel/schema/src/migration.rs FSM + " +
  "C66_schema_migration_window_exceeded) — reframed from 'acknowledged " +
  "debt/absent/C64 anticipated'; default path remains single-cycle " +
  "snapshot-rollback. (3) PROVENANCE ceremony status v3.1.1/v3.1.1.1 IN " +
  "PROGRESS→sealed + v3.1.1.2 added. (4) catechumenate 'empty' → scaffolding " +
  "present (0 sessions toward F21 unchanged). (5) Internal consistency: " +
  "catechumenate/INDEX.md §4 + HOW_TO_ADD_A_SESSION.md F21-gate made count-free " +
  "(stale '26 Active cards × 0.75 = 20' → defer to META §6.3 '75% of Active " +
  "Layer A cards'); META.md reading-order catechumenate note 'empty'→'form " +
  "scaffolding only (no sessions yet)'. DEPOSITS UNCHANGED — " +
  "descriptive-only per META §7. Chained from 7267dc58 (v3.1.1.1). " +
  "Production owner-key signature pending cultivator.";

// ---------------------------------------------------------------------------
// Prior provider — pinned hex (== v3.1.1.1 new_l0_hash).
// ---------------------------------------------------------------------------

/** Amendment prior provider: pinned hex equal to v3.1.1.1's new_l0_hash. */
export const getPriorL0Hash = priorFromPinnedHex(PRIOR_L0_HASH_HEX);

// ---------------------------------------------------------------------------
// Ceremony config.
// ---------------------------------------------------------------------------

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export const config: CeremonyConfig = {
  ceremony: "v3.1.1.2-descriptive-amendment",
  chainedFrom: "v3.1.1.1-p03-descriptive-amendment",
  diffSummary: DIFF_SUMMARY,
  dir: __dirname,
  tmpPrefix: "myco-v3_1_1_2",
  getPrior: getPriorL0Hash,
  priorManifest(): PriorManifestPinned {
    return {
      source:
        "v3.1.1.1 ceremony new_l0_hash (pinned in v3_1_1_1_p03_descriptive_amendment/manifest.json)",
      hash_hex: PRIOR_L0_HASH_HEX,
    };
  },
  priorLabel: "v3.1.1.1 new_l0_hash",
  newLabel: "BLAKE3 v3.1.1.2",
  startBannerSuffix: " (v3.1.1.2 amendment)",
};
