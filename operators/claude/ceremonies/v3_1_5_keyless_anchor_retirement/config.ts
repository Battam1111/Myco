// v3.1.5-keyless-anchor-retirement (AMENDMENT, ACTIVE) — ceremony config.
//
// Chains FROM the v3.1.4 ceremony's new_l0_hash (pinned hex). The L0 bundle-hash
// chain (each = BLAKE3 of canonical-bytes Map<rel_path, file_bytes> over
// docs/architecture/L0/**/*.md at that point):
//
//   cda9e2b3... (v3.1.1.2) -> 69456132... (v3.1.2) -> b22dca68... (v3.1.3) ->
//   8f37ec81... (v3.1.4) -> <new> (v3.1.5 bundle — this one)
//
// THE OWNER-KEY/ANCHOR RETIREMENT. Stages 1-5 removed all owner-key/anchor CODE
// (substrate Rust + Python kernel + the deleted anchor crate + the keyless TS
// operators); this amendment makes the DOCTRINE reflect the keyless reality:
// AS_anchor_surface card -> status:Superseded (tombstone in place; counts stay
// 28 cards / 36 files); the trust root is relocated to META §7.8 = the live
// human-in-the-loop at the CI gate + the substrate's causal DAG (P06) + the
// BLAKE3-sealed bundle (no owner signature). 8 Layer-C witnesses re-grounded
// keyless; detectors C12/C17/C20/C44/C50/C70 retired (numbers reserved);
// fixed-points F3/F4/F6/F23 deleted (F24/F5/F2/F16/C7 kept). Routine META §7.1
// amendment — no eternity-clause deposit touched. KEYLESS seal: the seal IS the
// BLAKE3 bundle hash; there is no owner signature.
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
 * Prior L0 hash for the v3.1.5-keyless-anchor-retirement ceremony — the v3.1.4
 * ceremony's new_l0_hash (pinned in v3_1_4_symbiotic_armor_identity/manifest.json
 * `new_l0.blake3_hex`).
 */
export const PRIOR_L0_HASH_HEX =
  "8f37ec81f78b3e5d7e0cf5943cf3a39f179301c9ec8932dcd4032ffea3d6bf4d";

/**
 * Diff summary stored verbatim in the ceremony record for v3.1.5. MUST match
 * manifest.json `diff_summary`.
 */
export const DIFF_SUMMARY =
  "L0 v3.1.5 amendment (KEYLESS owner-key/anchor retirement). Stages 1-5 removed " +
  "all owner-key/anchor CODE (substrate Rust + Python kernel + the deleted anchor " +
  "crate + the keyless TS operators); this amendment makes the DOCTRINE keyless. " +
  "AS_anchor_surface -> status:Superseded (tombstone in place; counts stay 28 " +
  "cards / 36 files). Trust root relocated to META §7.8 = the live human-in-the-loop " +
  "at the CI gate + the causal DAG (P06) + the BLAKE3-sealed bundle (no owner " +
  "signature). 8 Layer-C witnesses re-grounded to keyless tests (AS pos/neg -> " +
  "M-anchor-4 invariant-witness; P01 neg/edge + P03 edge -> keyless schema-evolution " +
  "+ classifier-path; P07 edge -> self_euthanasia_proposal; LB edge -> keyless " +
  "bet-retired-archive; COV06 neg -> c69_cultivation_orphaned_suppression_refused). " +
  "Detectors C12/C17/C20/C44/C50/C70 retired (numbers reserved); fixed-points " +
  "F3/F4/F6/F23 deleted; F24/F5/F2/F16/C7 kept. P01c substrate-ID formula keyless; " +
  "P06 §5.2 -> C7 Merkle re-derivation; P07 §3.5/§5.7 drill-auto-emit channel deleted " +
  "(self_euthanasia_proposal kept, §5.8 keyless MUST-NOT preserved); P08/COV05 spawn " +
  "keyless (C68 kept); P10.b invariant set keyless; COV06 heartbeat-staleness -> " +
  "acknowledged-debt; B047 dormant + B048 re-derived from P06; D-0046 retired + " +
  "D-0047 reframed keyless; META §7.8 headline + §3.4 anchor-layer row dropped. " +
  "Routine §7.1 (no eternity-clause deposit touched). Chained from 8f37ec81 " +
  "(v3.1.4-symbiotic-armor-identity). KEYLESS seal: the BLAKE3 bundle hash is the " +
  "seal; there is no owner signature.";

// ---------------------------------------------------------------------------
// Prior provider — pinned hex (== v3.1.4 new_l0_hash).
// ---------------------------------------------------------------------------

/** Amendment prior provider: pinned hex equal to v3.1.4's new_l0_hash. */
export const getPriorL0Hash = priorFromPinnedHex(PRIOR_L0_HASH_HEX);

// ---------------------------------------------------------------------------
// Ceremony config.
// ---------------------------------------------------------------------------

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export const config: CeremonyConfig = {
  ceremony: "v3.1.5-keyless-anchor-retirement",
  chainedFrom: "v3.1.4-symbiotic-armor-identity",
  diffSummary: DIFF_SUMMARY,
  dir: __dirname,
  tmpPrefix: "myco-v3_1_5",
  getPrior: getPriorL0Hash,
  priorManifest(): PriorManifestPinned {
    return {
      source:
        "v3.1.4 ceremony new_l0_hash (pinned in v3_1_4_symbiotic_armor_identity/manifest.json)",
      hash_hex: PRIOR_L0_HASH_HEX,
    };
  },
  priorLabel: "v3.1.4 new_l0_hash",
  newLabel: "BLAKE3 v3.1.5",
  startBannerSuffix: " (v3.1.5 keyless owner-key/anchor retirement)",
};
