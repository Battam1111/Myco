// v3.1-stratigraphy transition — full on-chain signing ceremony (thin wrapper).
//
// The end-to-end signing flow (boot anchor host + substrate → signL0Revision →
// verify DAG event → write ceremony_log) lives in ../_lib/ceremony.ts; the
// per-ceremony facts live in ./config.ts. This file is the thin CLI seam.
//
// Runs end-to-end:
//   1. Compute prior + new L0 hashes (drift is gated by verify_hashes.test.ts).
//   2. Spawn (or connect to) anchor_surface_host — owner Ed25519 key custody.
//   3. Spawn (or connect to) substrate — DAG host.
//   4. Call SubstrateClient.signL0Revision(prior, new, summary).
//   5. Verify the DAG event appears; capture event hash for archival.
//   6. Write ceremony_log/<timestamp>.json — the permanent off-chain record.
//
// Modes:
//   --mode dry-run    (default) — ephemeral sandbox: mkdtemp dirs, debug
//                                  binaries from target/debug, fresh owner key.
//   --mode production            — uses MYCO_STATE_DIR + MYCO_ANCHOR_SURFACE_DIR
//                                  + MYCO_SUBSTRATE_BIN + MYCO_ANCHOR_SURFACE_BIN
//                                  env vars. Connects to the real owner key.
//
// Operator instructions: see ./README.md.
// Per L0/cards/AS_anchor_surface §3.4 + M-anchor-5 §9.2.4.

import { fileURLToPath } from "node:url";

import {
  cliRun,
  runL0RevisionCeremony,
  type CeremonyResult,
  type Mode,
} from "../_lib/ceremony.ts";
import { config } from "./config.ts";

/** Run this ceremony for a given mode (back-compat signature). */
export const runCeremony = (mode: Mode): Promise<CeremonyResult> =>
  runL0RevisionCeremony(config, mode);

export { type CeremonyResult, type Mode };

// ---------------------------------------------------------------------------
// CLI entry.
// ---------------------------------------------------------------------------

const __filename = fileURLToPath(import.meta.url);
const invokedAsCli =
  process.argv[1] !== undefined && process.argv[1] === __filename;

if (invokedAsCli) {
  cliRun(config);
}
