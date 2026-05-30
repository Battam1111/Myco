// v3.1-stratigraphy transition — deterministic hash computation (thin wrapper).
//
// The hash machinery lives in ../_lib/bundle_hash.ts (computeNewL0Hash + the
// prior providers); the per-ceremony facts (commit/path/diff_summary, manifest
// prior_l0 shape) live in ./config.ts. This file is the thin seam that:
//   - re-exports the names the runner, the verify test, and the
//     `npm run ceremony:v3_1:hashes` script consume, and
//   - on direct CLI invocation, emits the manifest-shaped JSON via _lib's
//     emitManifestCli (genesis prior_l0 shape = {commit,path,byte_length,
//     sha256_hex}; NO chained_from).
//
// prior_l0_hash = SHA-256(git show e796451:docs/architecture/L0_VISION.md)
//               = the exact bytes of the DRAFT 9 SEALED monolith.
// new_l0_hash   = BLAKE3(canonical_bytes(Map<rel_path, file_bytes>)) over
//                 docs/architecture/L0/**/*.md.
//
// Per L1/HARD_RULES C18 canonical_bytes_render_drift (CRITICAL).

import { fileURLToPath } from "node:url";

import { computeNewL0Hash, getBundleFiles, REPO_ROOT } from "../_lib/bundle_hash.ts";
import { emitManifestCli } from "../_lib/ceremony.ts";
import {
  config,
  DIFF_SUMMARY,
  getPriorL0Hash,
  PRIOR_L0_COMMIT,
  PRIOR_L0_PATH,
} from "./config.ts";

// Re-exports for the runner, the verify test, and the npm hashes script.
export {
  computeNewL0Hash,
  getBundleFiles,
  REPO_ROOT,
  DIFF_SUMMARY,
  getPriorL0Hash,
  PRIOR_L0_COMMIT,
  PRIOR_L0_PATH,
};

/**
 * Back-compat alias: the genesis prior provider was historically named
 * `computePriorL0Hash` (it computes a SHA-256 from git history). Kept so any
 * external reference to the old name still resolves.
 */
export const computePriorL0Hash = getPriorL0Hash;

// ---------------------------------------------------------------------------
// CLI entry — `npm run ceremony:v3_1:hashes`.
// ---------------------------------------------------------------------------

// CLI detection — works cross-platform. process.argv[1] is the absolute path
// of the entry script (matches __filename when invoked directly).
const __filename = fileURLToPath(import.meta.url);
const invokedAsCli =
  process.argv[1] !== undefined && process.argv[1] === __filename;
if (invokedAsCli) {
  emitManifestCli(config);
}
