// v3.1.3-autonomy-and-detectors (AMENDMENT, ACTIVE) — ceremony config.
//
// This amendment chains FROM the v3.1.2 ceremony's new_l0_hash (a pinned hex).
// The L0 bundle-hash chain (each = BLAKE3 of canonical-bytes
// Map<rel_path, file_bytes> over docs/architecture/L0/**/*.md at that point):
//
//   798c047d... (v3.1.1) → 7267dc58... (v3.1.1.1) → cda9e2b3... (v3.1.1.2) →
//   69456132... (v3.1.2) → <new> (v3.1.3 bundle — this one)
//
// Amendment-shaped facts captured below:
//   - prior_l0_hash = pinned hex 69456132... (== v3.1.2 ceremony new_l0_hash),
//     via priorFromPinnedHex.
//   - manifest prior_l0 shape = { source, hash_hex }.
//   - has chained_from = "v3.1.2-witness-corpus".
//
// This is the Phase ①②③ amendment: descriptive debt→shipped + witness
// re-pointing. The cultivar's autonomy (production self-advance), proactive
// hunger (cultivar_initiated_ingestion_request) + starvation immune (C74), the
// now-fireable bet-weakening falsifiability quorum (C40) + reachable
// telos_drift_critical (C24) + cultivator_fiduciary_strain (C75) all SHIPPED;
// the ~7 nearest-available Layer-C witness slots replaced with exact-polarity
// tests; META §5.5 run-and-verify clause now LIVE via the test suite. Deposits +
// formulations UNCHANGED (descriptive only, META §7). This ceremony's
// verify_hashes test becomes the active drift gate in `npm test`.
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
 * Prior L0 hash for the v3.1.3-autonomy-and-detectors ceremony.
 *
 * This is the v3.1.2 ceremony's new_l0_hash (pinned in
 * v3_1_2_witness_corpus/manifest.json; also the production seal). Chains the
 * v3.1.3 amendment (Phase ①②③ debt→shipped + witness re-pointing) FROM the
 * v3.1.2 witness-corpus amendment.
 *
 * Chain so far:
 *   e796451 (DRAFT 9) → 5eacf3e7... (v3.1) → b1bec59a... (v3.1) →
 *   798c047d... (v3.1.1) → 7267dc58... (v3.1.1.1) → cda9e2b3... (v3.1.1.2) →
 *   69456132... (v3.1.2) → (this) v3.1.3
 */
export const PRIOR_L0_HASH_HEX =
  "6945613247fe6f7ab567cba59c9e7fbdd2fec2eb3b06f2f3a8f164decbc08fae";

/**
 * Diff summary stored verbatim in the signed envelope for v3.1.3. MUST match
 * manifest.json `diff_summary`. Changes to this string invalidate the
 * signature; bumping diff_summary requires a new ceremony.
 */
export const DIFF_SUMMARY =
  "L0 v3.1.3 descriptive amendment (Phase ①②③ — autonomy + detectors + " +
  "witness maturity): descriptive debt->shipped + Layer-C witness re-pointing; " +
  "DEPOSITS + FORMULATIONS UNCHANGED (META §7). (1) P04 §5.5/§10.3 production " +
  "self-advance SHIPPED (autonomous.rs::execute_self_driven_cycle_advance, " +
  "main.rs default-on, env-overridable) -> closes the 'request-driven service " +
  "not a cultivar' gap. (2) CHAR01 §4.3 / P02 §4.4 cultivar_initiated_ingestion_" +
  "request SHIPPED (ingest.rs::apply_hunger_and_emit, proactive hunger, " +
  "debounced). (3) P02 §8.1 / COV03 §3.4 p02_ingestion_starvation = C74. " +
  "(4) LB §3/§4 C40 bet_weakening_quorum now FIREABLE (rate-OLS direction over " +
  "first_difference_series + Z>=1.96; + birth-period suspension). (5) P14 §F " +
  "C24 telos_drift_critical reachable (grade re-partition: critical cos<=0.2). " +
  "(6) COV01 §3.5/§8.1 + META §7.7 cultivator_fiduciary_strain = C75 " +
  "(persistent telos_drift over 180d + cultivator inaction). (7) the ~7 " +
  "nearest-available Layer-C witness slots replaced with exact-polarity tests " +
  "(P02-neg C74, P14-neg C24, LB-neg C40, P04-neg self-advance, P05-neg C32, " +
  "P05-edge cold-tier, P07-edge owner-attested-destruction, P01c-edge handshake-" +
  "no-residue) + META §5.2/§5.5/§5.6 run-and-verify-polarity clause now LIVE " +
  "(every executable witness is run by `cargo test --workspace` each CI). " +
  "Chained from 69456132 (v3.1.2-witness-corpus). Production owner-key signature " +
  "by cultivator-delegated authority.";

// ---------------------------------------------------------------------------
// Prior provider — pinned hex (== v3.1.2 new_l0_hash).
// ---------------------------------------------------------------------------

/** Amendment prior provider: pinned hex equal to v3.1.2's new_l0_hash. */
export const getPriorL0Hash = priorFromPinnedHex(PRIOR_L0_HASH_HEX);

// ---------------------------------------------------------------------------
// Ceremony config.
// ---------------------------------------------------------------------------

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export const config: CeremonyConfig = {
  ceremony: "v3.1.3-autonomy-and-detectors",
  chainedFrom: "v3.1.2-witness-corpus",
  diffSummary: DIFF_SUMMARY,
  dir: __dirname,
  tmpPrefix: "myco-v3_1_3",
  getPrior: getPriorL0Hash,
  priorManifest(): PriorManifestPinned {
    return {
      source:
        "v3.1.2 ceremony new_l0_hash (pinned in v3_1_2_witness_corpus/manifest.json)",
      hash_hex: PRIOR_L0_HASH_HEX,
    };
  },
  priorLabel: "v3.1.2 new_l0_hash",
  newLabel: "BLAKE3 v3.1.3",
  startBannerSuffix: " (v3.1.3 autonomy + detectors + witnesses)",
};
