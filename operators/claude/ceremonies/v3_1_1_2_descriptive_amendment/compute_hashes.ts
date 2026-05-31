// v3.1.1.2-descriptive-amendment — deterministic hash computation
// (thin wrapper).
//
// The hash machinery lives in ../_lib/bundle_hash.ts; the per-ceremony facts
// (pinned prior hash, diff_summary, manifest prior_l0 shape) live in
// ./config.ts. This file is the thin seam that re-exports the names the
// runner, the verify test, and `npm run ceremony:v3_1_1_2:hashes` consume, and
// on direct CLI invocation emits the manifest-shaped JSON (amendment prior_l0
// shape = {source, hash_hex}; chained_from present) via _lib's emitManifestCli.
//
// This amendment chains FROM the v3.1.1.1 ceremony's new_l0_hash:
//   798c047d... (v3.1.1) → 7267dc58... (v3.1.1.1) → <new> (v3.1.1.2)
//
// Per L1/HARD_RULES C18 canonical_bytes_render_drift (CRITICAL).

import { fileURLToPath } from "node:url";

import { computeNewL0Hash, getBundleFiles, REPO_ROOT } from "../_lib/bundle_hash.ts";
import { emitManifestCli } from "../_lib/ceremony.ts";
import { config, DIFF_SUMMARY, getPriorL0Hash, PRIOR_L0_HASH_HEX } from "./config.ts";

// Re-exports for the runner, the verify test, and the npm hashes script.
export {
  computeNewL0Hash,
  getBundleFiles,
  REPO_ROOT,
  DIFF_SUMMARY,
  getPriorL0Hash,
  PRIOR_L0_HASH_HEX,
};

// ---------------------------------------------------------------------------
// CLI entry — `npm run ceremony:v3_1_1_2:hashes`.
// ---------------------------------------------------------------------------

const __filename = fileURLToPath(import.meta.url);
const invokedAsCli =
  process.argv[1] !== undefined && process.argv[1] === __filename;
if (invokedAsCli) {
  emitManifestCli(config);
}
