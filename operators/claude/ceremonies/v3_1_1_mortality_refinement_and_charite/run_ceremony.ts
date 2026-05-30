// v3.1.1-mortality-refinement-and-charite — full on-chain signing ceremony
// (thin wrapper).
//
// The end-to-end signing flow lives in ../_lib/ceremony.ts; the per-ceremony
// facts live in ./config.ts. This file is the thin CLI seam.
//
// Runs end-to-end (chained from v3.1 ceremony's new_l0_hash):
//   1. Compute prior + new L0 hashes (drift gated by verify_hashes.test.ts).
//   2. Spawn (or connect to) anchor_surface_host — owner Ed25519 key custody.
//   3. Spawn (or connect to) substrate — DAG host.
//   4. signL0Revision(prior=v3.1_new, new=v3.1.1, summary).
//   5. Verify the DAG event appears; capture event hash for archival.
//   6. Write ceremony_log/<timestamp>.json — the permanent off-chain record.
//
// Modes: --mode dry-run (default) | --mode production (env-driven paths).

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
