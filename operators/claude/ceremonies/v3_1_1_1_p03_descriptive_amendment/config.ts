// v3.1.1.1-p03-descriptive-amendment (AMENDMENT, ACTIVE) — ceremony config.
//
// This amendment chains FROM the v3.1.1 ceremony's new_l0_hash (a pinned hex).
// The L0 bundle-hash chain (each = BLAKE3 of canonical-bytes
// Map<rel_path, file_bytes> over docs/architecture/L0/**/*.md at that point):
//
//   b1bec59a... (v3.1 bundle) → 798c047d... (v3.1.1 bundle) →
//   7267dc58... (v3.1.1.1 bundle — this one; LF-normalized seal)
//
// Amendment-shaped facts captured below:
//   - prior_l0_hash = pinned hex 798c047d... (== v3.1.1 ceremony new_l0_hash),
//     via priorFromPinnedHex.
//   - manifest prior_l0 shape = { source, hash_hex }.
//   - has chained_from = "v3.1.1-mortality-refinement-and-charite".
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
 * Prior L0 hash for the v3.1.1.1 descriptive-amendment ceremony.
 *
 * This is the v3.1.1 ceremony's new_l0_hash (pinned in
 * v3_1_1_mortality_refinement_and_charite/manifest.json). Chains the v3.1.1.1
 * descriptive amendment (Sprint 6.D's P03 §3.3 reframe) FROM the v3.1.1
 * mortality+charite amendment.
 *
 * Chain so far:
 *   e796451 (DRAFT 9) → 5eacf3e7... (v3.1) → b1bec59a... (v3.1) →
 *   798c047d... (v3.1.1) → (this) v3.1.1.1
 */
export const PRIOR_L0_HASH_HEX =
  "798c047d592730e20375429706bde1dea3f3da26394891a0a3055de004dff824";

/**
 * Diff summary stored verbatim in the signed envelope for v3.1.1.1. MUST match
 * manifest.json `diff_summary`. Changes to this string invalidate the
 * signature; bumping diff_summary requires a new ceremony.
 *
 * VERBATIM — byte-for-byte identical to the original compute_hashes.ts.
 */
export const DIFF_SUMMARY =
  "L0 v3.1.1.1 descriptive amendment (Sprint 6.D + Sprint 7.I): " +
  "(Sprint 6.D) " +
  "P03_resumable_evolution.md amended (version 2.1 → 3) to align " +
  "doctrine with shipping behavior. Specific changes: " +
  "(1) §3.3 reframed from 'two-phase migration (L1/SCHEMA §1.3)' to " +
  "'snapshot-rollback semantics' — describes actual " +
  "kernel/governance/.../schema_evolution.py::apply_schema_diff " +
  "implementation (snapshot → apply → I3 validate → commit-or-restore " +
  "in one cycle). " +
  "(2) §4.3 cascading update from 'candidate alongside current; M " +
  "consecutive cycles' to 'single-cycle snapshot-rollback apply' with " +
  "reference to §10.4 acknowledged debt. " +
  "(3) §5.2 wording adjustment: 'MUST NOT apply schema mutations " +
  "without two-phase migration' → 'MUST NOT apply schema mutations " +
  "OUTSIDE the snapshot-rollback envelope'. " +
  "(4) §7.1 M1 misreading clarified to honor both shipping behavior " +
  "AND target M-cycle migration. " +
  "(5) §10.4 NEW 'Acknowledged debt — multi-cycle two-phase " +
  "migration' section added: describes shipping state, target " +
  "enhancement, 5-step migration path (kernel/schema/src/migration.rs " +
  "two_phase_commit types + substrate bookkeeping + classifier " +
  "extensions + operator surface + C64 anticipated). " +
  "(6) §12 structural_anchors: phantom " +
  "`kernel/schema/src/migration.rs::two_phase_commit` (file never " +
  "existed) replaced by actual " +
  "`kernel/governance/.../schema_evolution.py::apply_schema_diff`. " +
  "DEPOSIT (P03 §2) UNCHANGED — `first-class mutable + " +
  "rollback-protected` honored by both shipping snapshot-rollback " +
  "AND planned M-cycle migration. Descriptive-amend per META §7; " +
  "deposit_immutable: false on P03 permits this non-deposit refinement. " +
  "(Sprint 7.I) Cross-reference path-drift cleanup across L0 + L1 + L2 + " +
  "L3 + algorithms + diagrams docs: all `L0/cards/<NAME> §X.Y` references " +
  "updated to `L0/cards/<NAME>.md §X.Y` form per L0/README.md §" +
  "\"What's still missing\" item 5. 22 files touched, ~70 references " +
  "updated. No deposit changes. Pure housekeeping per META §7. " +
  "(Sprint 7.H) Layer D catechumenate scaffolding: TEMPLATE.md (META §6.1 " +
  "session form template) + HOW_TO_ADD_A_SESSION.md (practical workflow " +
  "guide for cultivator-A + successor candidate). Zero sessions count " +
  "toward F21 activation — these are infrastructure files, not " +
  "catechumenate sessions. " +
  "Sealed 2026-05-19 (Sprint 6.D commit af6ef3b + Sprint 7.B/7.D/7.H/7.I).";

// ---------------------------------------------------------------------------
// Prior provider — pinned hex (== v3.1.1 new_l0_hash).
// ---------------------------------------------------------------------------

/** Amendment prior provider: pinned hex equal to v3.1.1's new_l0_hash. */
export const getPriorL0Hash = priorFromPinnedHex(PRIOR_L0_HASH_HEX);

// ---------------------------------------------------------------------------
// Ceremony config.
// ---------------------------------------------------------------------------

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export const config: CeremonyConfig = {
  ceremony: "v3.1.1.1-p03-descriptive-amendment",
  chainedFrom: "v3.1.1-mortality-refinement-and-charite",
  diffSummary: DIFF_SUMMARY,
  dir: __dirname,
  tmpPrefix: "myco-v3_1_1_1",
  getPrior: getPriorL0Hash,
  priorManifest(): PriorManifestPinned {
    return {
      source:
        "v3.1.1 ceremony new_l0_hash (pinned in v3_1_1_mortality_refinement_and_charite/manifest.json)",
      hash_hex: PRIOR_L0_HASH_HEX,
    };
  },
  priorLabel: "v3.1.1 new_l0_hash",
  newLabel: "BLAKE3 v3.1.1.1",
  startBannerSuffix: " (v3.1.1.1 amendment)",
};
