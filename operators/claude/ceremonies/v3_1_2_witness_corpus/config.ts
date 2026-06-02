// v3.1.2-witness-corpus (AMENDMENT, ACTIVE) — ceremony config.
//
// This amendment chains FROM the v3.1.1.2 ceremony's new_l0_hash (a pinned hex).
// The L0 bundle-hash chain (each = BLAKE3 of canonical-bytes
// Map<rel_path, file_bytes> over docs/architecture/L0/**/*.md at that point):
//
//   b1bec59a... (v3.1) → 798c047d... (v3.1.1) → 7267dc58... (v3.1.1.1) →
//   cda9e2b3... (v3.1.1.2) → <new> (v3.1.2 bundle — this one)
//
// Amendment-shaped facts captured below:
//   - prior_l0_hash = pinned hex cda9e2b3... (== v3.1.1.2 ceremony new_l0_hash),
//     via priorFromPinnedHex.
//   - manifest prior_l0 shape = { source, hash_hex }.
//   - has chained_from = "v3.1.1.2-descriptive-amendment".
//
// This is the v0.9.x Layer C witness-corpus milestone (META §5.2/§5.5/§5.6): the
// 28 cards' witnesses are re-pointed from the never-created `tests/integration/*`
// placeholders to real substrate tests (executable) / canonical dilemmas
// (narrative), a `kind:` discriminator is added, structural anchors are de-danged,
// the §5.5 existence-level witness-lint ships with C67 `doctrine_witness_drift`,
// and the shipped-but-"to be added" markers in P07/CHAR07/P05 are scrubbed. This
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
 * Prior L0 hash for the v3.1.2-witness-corpus ceremony.
 *
 * This is the v3.1.1.2 ceremony's new_l0_hash (pinned in
 * v3_1_1_2_descriptive_amendment/manifest.json). Chains the v3.1.2 witness-corpus
 * amendment (Layer C witness re-pointing + kind: discriminator + §5.5 lint)
 * FROM the v3.1.1.2 descriptive amendment.
 *
 * Chain so far:
 *   e796451 (DRAFT 9) → 5eacf3e7... (v3.1) → b1bec59a... (v3.1) →
 *   798c047d... (v3.1.1) → 7267dc58... (v3.1.1.1) → cda9e2b3... (v3.1.1.2) →
 *   (this) v3.1.2
 */
export const PRIOR_L0_HASH_HEX =
  "cda9e2b32d505ae1a5acb2d4d71282f63385381c07b8fa3f845f6d2bad033784";

/**
 * Diff summary stored verbatim in the signed envelope for v3.1.2. MUST match
 * manifest.json `diff_summary`. Changes to this string invalidate the
 * signature; bumping diff_summary requires a new ceremony.
 */
export const DIFF_SUMMARY =
  "L0 v3.1.2 witness-corpus amendment: the v0.9.x Layer C witness milestone " +
  "(META §5.2/§5.5/§5.6). (1) All 28 cards' `witnesses:` re-pointed from the " +
  "never-created `tests/integration/*` placeholders to real artifacts + a " +
  "`kind: executable|narrative` discriminator: 16 executable cards " +
  "(P01,P01c,P02-P11,P14,AS,LB,COV06) -> runnable substrate test fns; 12 " +
  "narrative cards (CHAR01-07,COV01-05) -> canonical_dilemma_corpus references. " +
  "(2) structural_anchors de-danged to real homes (server.rs->server/, " +
  "events.rs->events/<mod>, ghost paths->real). (3) §5.5 existence-level " +
  "witness-lint shipped (operators/claude/tests/witness_lint.test.ts) + C67 " +
  "doctrine_witness_drift assigned as its CI-lint signal (not a runtime " +
  "detector). (4) descriptive scrubs of shipped-but-marked-'to be added in " +
  "v3.1.1 cascade' content: P07 §12-14 (internal_mortality/prune anchors + " +
  "B051-B055 + D-0050/D-0053), CHAR07 §13-15 + front-matter (B056-B060 + " +
  "D-0050/51/52/54 + char07.rs/observatory.rs anchors), P05 §3.4 dead 'P15' ref. " +
  "(5) PROVENANCE §6.2 + §8: backup-encryption debt marked implemented " +
  "(at_rest_seal.rs DPAPI + backup_encryption.rs, L1/SKIN §8); Layer C witness " +
  "debt -> shipped. DEPOSITS + FORMULATIONS UNCHANGED — Layer C / descriptive " +
  "only per META §7. ~7 nearest-available exact-witness slots + the " +
  "run-and-verify-polarity lint clause remain staged per §5.6. Chained from " +
  "cda9e2b3 (v3.1.1.2). Production owner-key signature pending cultivator.";

// ---------------------------------------------------------------------------
// Prior provider — pinned hex (== v3.1.1.2 new_l0_hash).
// ---------------------------------------------------------------------------

/** Amendment prior provider: pinned hex equal to v3.1.1.2's new_l0_hash. */
export const getPriorL0Hash = priorFromPinnedHex(PRIOR_L0_HASH_HEX);

// ---------------------------------------------------------------------------
// Ceremony config.
// ---------------------------------------------------------------------------

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export const config: CeremonyConfig = {
  ceremony: "v3.1.2-witness-corpus",
  chainedFrom: "v3.1.1.2-descriptive-amendment",
  diffSummary: DIFF_SUMMARY,
  dir: __dirname,
  tmpPrefix: "myco-v3_1_2",
  getPrior: getPriorL0Hash,
  priorManifest(): PriorManifestPinned {
    return {
      source:
        "v3.1.1.2 ceremony new_l0_hash (pinned in v3_1_1_2_descriptive_amendment/manifest.json)",
      hash_hex: PRIOR_L0_HASH_HEX,
    };
  },
  priorLabel: "v3.1.1.2 new_l0_hash",
  newLabel: "BLAKE3 v3.1.2",
  startBannerSuffix: " (v3.1.2 witness-corpus)",
};
