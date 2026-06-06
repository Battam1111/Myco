// Shared L0-revision ceremony machinery (keyless, v3.1.5).
//
// Every L0-revision "ceremony" records the doctrine bundle's BLAKE3 hash; only a
// handful of per-ceremony facts differ (the ceremony name, what it chains from,
// the prior-hash provider, the diff summary, the manifest prior_l0 shape, and a
// few cosmetic log labels). Those facts are captured in `CeremonyConfig` (see
// each ceremony's `config.ts`); this module holds the invariant machinery:
//
//   parseMode                      — CLI mode flag (cosmetic; both modes compute).
//   runL0RevisionCeremony(cfg,mode)— compute the prior+new bundle hash and return
//                                     the CeremonyResult.
//   cliRun(cfg)                    — the run_ceremony.ts CLI entry: run, write
//                                     ceremony_log/<ts>.json, print.
//   emitManifestCli(cfg)           — the compute_hashes.ts CLI entry: print the
//                                     manifest-shaped JSON.
//
// v3.1.5: the owner-key / anchor signing layer was REMOVED. The seal IS the
// computed BLAKE3 bundle hash, recorded in manifest.json + the git commit; the
// drift gate (verify_hashes.test.ts) re-derives it from the bundle. There is no
// owner signature, no anchor, and no substrate DAG event.

import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import {
  computeNewL0Hash,
  NEW_L0_ROOT,
  type PriorL0Hash,
} from "./bundle_hash.ts";

// ---------------------------------------------------------------------------
// Mode parsing.
// ---------------------------------------------------------------------------

export type Mode = "dry-run" | "production";

export function parseMode(): Mode {
  const argIdx = process.argv.indexOf("--mode");
  if (argIdx === -1) return "dry-run";
  const v = process.argv[argIdx + 1];
  if (v !== "dry-run" && v !== "production") {
    throw new Error(`unknown --mode value: ${v} (expected dry-run | production)`);
  }
  return v;
}

// ---------------------------------------------------------------------------
// Manifest prior_l0 shapes.
// ---------------------------------------------------------------------------

/** Genesis manifest prior_l0 shape (SHA-256 of a git-history file). */
export interface PriorManifestGit {
  commit: string;
  path: string;
  byte_length: number;
  sha256_hex: string;
}

/** Amendment manifest prior_l0 shape (pinned hex == prior ceremony new_l0_hash). */
export interface PriorManifestPinned {
  source: string;
  hash_hex: string;
}

export type PriorManifest = PriorManifestGit | PriorManifestPinned;

// ---------------------------------------------------------------------------
// CeremonyConfig — the per-ceremony facts.
// ---------------------------------------------------------------------------

export interface CeremonyConfig {
  /** Locked ceremony name (e.g. "v3.1-stratigraphy-transition"). */
  ceremony: string;
  /** The ceremony this chains from, or null for the genesis transition. */
  chainedFrom: string | null;
  /** Verbatim diff summary; MUST match manifest.diff_summary byte-for-byte. */
  diffSummary: string;
  /** Absolute path of this ceremony's directory (for ceremony_log + manifest). */
  dir: string;
  /** mkdtemp prefix (retained for config compatibility; unused since v3.1.5). */
  tmpPrefix: string;
  /** Prior-hash provider (priorFromGitSha256 or priorFromPinnedHex). */
  getPrior: () => PriorL0Hash;
  /** Build the manifest prior_l0 object (shape branches on ceremony kind). */
  priorManifest(): PriorManifest;
  /** Cosmetic stderr label for the prior hash (e.g. "SHA-256 @ e796451"). */
  priorLabel: string;
  /** Cosmetic stderr label for the new hash (e.g. "BLAKE3 v3.1"). */
  newLabel: string;
  /** Cosmetic suffix on the CLI start banner. */
  startBannerSuffix: string;
}

// ---------------------------------------------------------------------------
// CeremonyResult (keyless).
// ---------------------------------------------------------------------------

/**
 * Result of a single keyless ceremony run.
 *
 * `ceremony` / `chained_from` are OPTIONAL: the genesis transition omits them;
 * amendments populate both. The signed/on-chain fields (signer pubkey, anchor
 * nonce + timestamp, l0_revision DAG event hash) were removed with the anchor
 * layer in v3.1.5 — the seal is the bundle hash alone.
 */
export interface CeremonyResult {
  mode: Mode;
  ceremony?: string;
  chained_from?: string;
  prior_l0_hash_hex: string;
  new_l0_hash_hex: string;
  diff_summary: string;
  bundle_files: number;
  canonical_bytes_length: number;
  ceremony_started_at_iso: string;
  ceremony_completed_at_iso: string;
}

// ---------------------------------------------------------------------------
// Ceremony runner (keyless).
// ---------------------------------------------------------------------------

export async function runL0RevisionCeremony(
  cfg: CeremonyConfig,
  mode: Mode,
): Promise<CeremonyResult> {
  const startedAt = new Date().toISOString();

  // Compute prior + new bundle hash. The new_l0_hash IS the seal.
  const prior = cfg.getPrior();
  const next = computeNewL0Hash();

  process.stderr.write(
    `[ceremony:${mode}] prior_l0_hash (${cfg.priorLabel}) = ${prior.hashHex}\n` +
      `[ceremony:${mode}] new_l0_hash   (${cfg.newLabel})      = ${next.hashHex}\n` +
      `[ceremony:${mode}] bundle files: ${next.bundleFiles.length}, ` +
      `canonical bytes: ${next.canonicalBytesLength}\n`,
  );

  const completedAt = new Date().toISOString();

  // Keyless (v3.1.5): the seal IS the computed BLAKE3 bundle hash above,
  // recorded in manifest.json + the git commit. No owner signature, no anchor,
  // no substrate DAG event; the drift gate re-derives the hash from the bundle.
  const base: CeremonyResult = {
    mode,
    prior_l0_hash_hex: prior.hashHex,
    new_l0_hash_hex: next.hashHex,
    diff_summary: cfg.diffSummary,
    bundle_files: next.bundleFiles.length,
    canonical_bytes_length: next.canonicalBytesLength,
    ceremony_started_at_iso: startedAt,
    ceremony_completed_at_iso: completedAt,
  };

  if (cfg.chainedFrom !== null) {
    return {
      mode,
      ceremony: cfg.ceremony,
      chained_from: cfg.chainedFrom,
      ...stripMode(base),
    };
  }
  return base;
}

/** Drop `mode` from a CeremonyResult (it is re-emitted first by the caller). */
function stripMode(r: CeremonyResult): Omit<CeremonyResult, "mode"> {
  const { mode: _mode, ...rest } = r;
  return rest;
}

// ---------------------------------------------------------------------------
// run_ceremony.ts CLI entry.
// ---------------------------------------------------------------------------

function ceremonyLogPath(cfg: CeremonyConfig, mode: Mode, completedAtIso: string): string {
  const logDir = join(cfg.dir, "ceremony_log");
  if (!existsSync(logDir)) mkdirSync(logDir, { recursive: true });
  // Filesystem-safe timestamp.
  const stamp = completedAtIso.replace(/[:.]/g, "-");
  return join(logDir, `${mode}_${stamp}.json`);
}

/**
 * The run_ceremony.ts CLI entry. Parses --mode, runs the keyless ceremony,
 * writes the permanent off-chain ceremony_log record, prints the human summary
 * to stderr and the single-line JSON result to stdout. Exits 0 on success.
 */
export function cliRun(cfg: CeremonyConfig): void {
  const mode = parseMode();
  process.stderr.write(`[ceremony] mode=${mode} starting${cfg.startBannerSuffix}...\n`);

  runL0RevisionCeremony(cfg, mode)
    .then((res) => {
      const logPath = ceremonyLogPath(cfg, mode, res.ceremony_completed_at_iso);
      writeFileSync(logPath, JSON.stringify(res, null, 2) + "\n");
      process.stderr.write(
        `[ceremony] SEALED (keyless)\n` +
          `[ceremony] new_l0_hash   = ${res.new_l0_hash_hex}\n` +
          `[ceremony] bundle files  = ${res.bundle_files}\n` +
          `[ceremony] log written to: ${logPath}\n`,
      );
      // Single-line JSON to stdout for machine consumption.
      process.stdout.write(JSON.stringify(res) + "\n");
      process.exit(0);
    })
    .catch((err) => {
      process.stderr.write(
        `[ceremony] FAILED: ${err instanceof Error ? err.message : String(err)}\n`,
      );
      if (err instanceof Error && err.stack) {
        process.stderr.write(err.stack + "\n");
      }
      process.exit(1);
    });
}

// ---------------------------------------------------------------------------
// compute_hashes.ts CLI entry — emit the manifest-shaped JSON.
// ---------------------------------------------------------------------------

/**
 * The compute_hashes.ts CLI entry. Prints the manifest-shaped JSON for this
 * ceremony to stdout. The `prior_l0` block shape and the presence of
 * `chained_from` branch on whether the ceremony chains (amendment) or is the
 * genesis transition.
 */
export function emitManifestCli(cfg: CeremonyConfig): void {
  const next = computeNewL0Hash();
  const prior_l0 = cfg.priorManifest();

  const out: Record<string, unknown> = {
    schema_version: 1,
    ceremony: cfg.ceremony,
  };
  if (cfg.chainedFrom !== null) {
    out.chained_from = cfg.chainedFrom;
  }
  out.prior_l0 = prior_l0;
  out.new_l0 = {
    root: NEW_L0_ROOT,
    bundle_files: next.bundleFiles,
    canonical_bytes_length: next.canonicalBytesLength,
    blake3_hex: next.hashHex,
  };
  out.diff_summary = cfg.diffSummary;

  process.stdout.write(JSON.stringify(out, null, 2) + "\n");
}
