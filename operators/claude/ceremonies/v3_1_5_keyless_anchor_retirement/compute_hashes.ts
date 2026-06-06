// v3.1.5-keyless-anchor-retirement — deterministic hash computation (thin wrapper).
//
// The hash machinery lives in ../_lib/bundle_hash.ts; the per-ceremony facts
// live in ./config.ts. On direct CLI invocation emits the manifest-shaped JSON
// via _lib's emitManifestCli.
//
//   b22dca68... (v3.1.3) -> 8f37ec81... (v3.1.4) -> <new> (v3.1.5)
//
// Per L1/HARD_RULES C18 canonical_bytes_render_drift (CRITICAL).

import { fileURLToPath } from "node:url";

import { computeNewL0Hash, getBundleFiles, REPO_ROOT } from "../_lib/bundle_hash.ts";
import { emitManifestCli } from "../_lib/ceremony.ts";
import { config, DIFF_SUMMARY, getPriorL0Hash, PRIOR_L0_HASH_HEX } from "./config.ts";

export {
  computeNewL0Hash,
  getBundleFiles,
  REPO_ROOT,
  DIFF_SUMMARY,
  getPriorL0Hash,
  PRIOR_L0_HASH_HEX,
};

const __filename = fileURLToPath(import.meta.url);
const invokedAsCli =
  process.argv[1] !== undefined && process.argv[1] === __filename;
if (invokedAsCli) {
  emitManifestCli(config);
}
