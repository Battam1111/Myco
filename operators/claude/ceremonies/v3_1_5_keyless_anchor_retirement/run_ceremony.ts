// v3.1.5-keyless-anchor-retirement — ceremony runner (thin wrapper, keyless).
//
// The keyless ceremony flow lives in ../_lib/ceremony.ts; the per-ceremony facts
// live in ./config.ts. v3.1.5 itself retired the owner-key/anchor, so the seal
// is purely the BLAKE3 bundle hash (no anchor boot, no owner signature, no
// substrate DAG event). Modes: --mode dry-run (default) | --mode production
// (both compute + record the same keyless seal).

import { fileURLToPath } from "node:url";

import {
  cliRun,
  runL0RevisionCeremony,
  type CeremonyResult,
  type Mode,
} from "../_lib/ceremony.ts";
import { config } from "./config.ts";

/** Run this ceremony for a given mode. */
export const runCeremony = (mode: Mode): Promise<CeremonyResult> =>
  runL0RevisionCeremony(config, mode);

export { type CeremonyResult, type Mode };

const __filename = fileURLToPath(import.meta.url);
const invokedAsCli =
  process.argv[1] !== undefined && process.argv[1] === __filename;

if (invokedAsCli) {
  cliRun(config);
}
