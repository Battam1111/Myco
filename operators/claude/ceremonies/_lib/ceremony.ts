// Shared on-chain signing machinery for L0-revision ceremonies.
//
// Every L0-revision ceremony (genesis transition + each amendment) runs the
// same end-to-end flow; only a handful of per-ceremony facts differ (the
// ceremony name, what it chains from, the prior-hash provider, the diff
// summary, the manifest prior_l0 shape, and a few cosmetic log labels). Those
// facts are captured in `CeremonyConfig` (see each ceremony's `config.ts`);
// this module holds the invariant machinery they share:
//
//   parseMode / locateBinary       — CLI + binary discovery (mirrors
//                                     tests/substrate_client.test.ts).
//   runL0RevisionCeremony(cfg,mode)— boot anchor host + substrate, sign the
//                                     L0 revision, verify the DAG event,
//                                     return the CeremonyResult.
//   cliRun(cfg)                    — the run_ceremony.ts CLI entry: run, write
//                                     ceremony_log/<ts>.json, print.
//   emitManifestCli(cfg)           — the compute_hashes.ts CLI entry: print
//                                     the manifest-shaped JSON (prior_l0 shape
//                                     branches on whether cfg chains or not).
//
// The shared verify_hashes.test.ts assertions live in ./verify.ts (kept
// separate so this CLI machinery's import graph never pulls in `node:test`).
//
// Per L0/cards/AS_anchor_surface §3.4 + M-anchor-5 §9.2.4.

import {
  existsSync,
  mkdirSync,
  mkdtempSync,
  rmSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve as resolvePath } from "node:path";

import { SubstrateClient } from "../../src/substrate_client.ts";
import { OperatorIdentity } from "../../src/operator_identity.ts";
import { killAllSpawnedHosts } from "../../src/anchor_surface_client.ts";

import {
  bytesToHex,
  computeNewL0Hash,
  NEW_L0_ROOT,
  REPO_ROOT,
  type PriorL0Hash,
} from "./bundle_hash.ts";

// ---------------------------------------------------------------------------
// Mode parsing + binary discovery.
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

export function locateBinary(
  envVar: string,
  debugName: string,
  repoRoot: string,
): string {
  const fromEnv = process.env[envVar];
  if (fromEnv && existsSync(fromEnv)) return fromEnv;
  const exe = process.platform === "win32" ? ".exe" : "";
  const candidate = resolvePath(repoRoot, "target", "debug", `${debugName}${exe}`);
  if (existsSync(candidate)) return candidate;
  throw new Error(
    `${debugName} binary not found at ${candidate}; build first with ` +
      `\`cargo build -p ${debugName}\` or set ${envVar}=/path/to/binary`,
  );
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
  /** mkdtemp prefix for ephemeral dry-run dirs (e.g. "myco-v3_1"). */
  tmpPrefix: string;
  /** Prior-hash provider (priorFromGitSha256 or priorFromPinnedHex). */
  getPrior: () => PriorL0Hash;
  /** Build the manifest prior_l0 object (shape branches on ceremony kind). */
  priorManifest(): PriorManifest;
  /** Cosmetic stderr label for the prior hash (e.g. "SHA-256 @ e796451"). */
  priorLabel: string;
  /** Cosmetic stderr label for the new hash (e.g. "BLAKE3 v3.1"). */
  newLabel: string;
  /**
   * Cosmetic suffix on the CLI start banner. Genesis: "". Amendments:
   * " (v3.1.1 amendment)" etc.
   */
  startBannerSuffix: string;
}

// ---------------------------------------------------------------------------
// CeremonyResult.
// ---------------------------------------------------------------------------

/**
 * Result of a single ceremony run.
 *
 * `ceremony` / `chained_from` are OPTIONAL: the genesis transition omits them
 * (its result has no such fields); amendments populate both. The runner adds
 * them iff `cfg.chainedFrom !== null` so genesis output stays byte-identical.
 */
export interface CeremonyResult {
  mode: Mode;
  ceremony?: string;
  chained_from?: string;
  prior_l0_hash_hex: string;
  new_l0_hash_hex: string;
  diff_summary: string;
  accepted: boolean;
  classification: string;
  mutation_type: string;
  l0_revision_event_hash_hex: string;
  l0_revision_node_type: string;
  signer_public_key_hex: string;
  anchor_timestamp_unix_ns: string; // bigint serialized
  anchor_nonce_hex: string;
  ceremony_started_at_iso: string;
  ceremony_completed_at_iso: string;
}

// ---------------------------------------------------------------------------
// Ceremony runner.
// ---------------------------------------------------------------------------

export async function runL0RevisionCeremony(
  cfg: CeremonyConfig,
  mode: Mode,
): Promise<CeremonyResult> {
  const startedAt = new Date().toISOString();

  // Step 1 — compute hashes (drift check happens via verify_hashes test; here
  // we just bind the values that get signed).
  const prior = cfg.getPrior();
  const next = computeNewL0Hash();

  process.stderr.write(
    `[ceremony:${mode}] prior_l0_hash (${cfg.priorLabel}) = ${prior.hashHex}\n` +
      `[ceremony:${mode}] new_l0_hash   (${cfg.newLabel})      = ${next.hashHex}\n` +
      `[ceremony:${mode}] bundle files: ${next.bundleFiles.length}, ` +
      `canonical bytes: ${next.canonicalBytesLength}\n`,
  );

  // Step 2 — locate binaries. REPO_ROOT (from bundle_hash, derived from
  // _lib/__dirname) resolves to the same absolute workspace root the original
  // per-ceremony run_ceremony.ts used, since _lib sits at the same depth.
  const substrateBin = locateBinary("MYCO_SUBSTRATE_BIN", "myco-substrate", REPO_ROOT);
  const anchorBin = locateBinary(
    "MYCO_ANCHOR_SURFACE_BIN",
    "anchor-surface-host",
    REPO_ROOT,
  );

  // Step 3 — owner identity + state dirs.
  const ephemeral = mode === "dry-run";
  const opDir = ephemeral
    ? mkdtempSync(resolvePath(tmpdir(), `${cfg.tmpPrefix}-anchor-`))
    : process.env.MYCO_ANCHOR_SURFACE_DIR ??
      (() => {
        throw new Error(
          "production mode requires MYCO_ANCHOR_SURFACE_DIR pointing at the owner key dir",
        );
      })();
  const stateDir = ephemeral
    ? mkdtempSync(resolvePath(tmpdir(), `${cfg.tmpPrefix}-state-`))
    : process.env.MYCO_STATE_DIR ??
      (() => {
        throw new Error(
          "production mode requires MYCO_STATE_DIR pointing at the substrate state dir",
        );
      })();

  process.stderr.write(
    `[ceremony:${mode}] anchor dir: ${opDir}\n` +
      `[ceremony:${mode}] state dir:  ${stateDir}\n`,
  );

  try {
    // Step 4 — boot anchor host + substrate.
    const identity = await OperatorIdentity.loadOrCreate(opDir, {
      hostBinary: anchorBin,
    });
    const signerPubkey = identity.publicKeyBytes();

    const client = await SubstrateClient.spawn({
      substrateBinary: substrateBin,
      env: { MYCO_STATE_DIR: stateDir },
      operatorIdentity: identity,
    });

    try {
      // Step 5 — sign + submit.
      const wallClock = await identity.getAnchorWallClock();
      const nonceResult = await identity.generateAnchorNonce(300n);

      const result = await client.signL0Revision({
        priorL0Hash: prior.hash,
        newL0Hash: next.hash,
        diffSummary: cfg.diffSummary,
        operatorIdentity: identity,
      });

      if (!result.accepted) {
        throw new Error(
          `signL0Revision REJECTED: ${result.rejectionReason ?? "<no reason>"}`,
        );
      }

      if (!result.l0RevisionEventHash) {
        throw new Error("substrate accepted but did not surface l0RevisionEventHash");
      }

      // Step 6 — verify DAG event appeared.
      // Substrate emits `l0_revision_attested:{first_8_bytes_hex}` (16 hex chars)
      // per substrate/src/events.rs::l0_revision_attested_node_type.
      const nodes = await client.queryRecentNodes(50n, "l0_revision_attested:");
      const priorPrefix = prior.hashHex.slice(0, 16);
      const expectedNodeType = `l0_revision_attested:${priorPrefix}`;
      const found = nodes.nodes.find((n) => n.nodeType === expectedNodeType);
      if (!found) {
        throw new Error(
          `${expectedNodeType} not found in recent DAG nodes. ` +
            `Saw: ${nodes.nodes.map((n) => n.nodeType).join(", ")}`,
        );
      }

      const completedAt = new Date().toISOString();
      const base: CeremonyResult = {
        mode,
        prior_l0_hash_hex: prior.hashHex,
        new_l0_hash_hex: next.hashHex,
        diff_summary: cfg.diffSummary,
        accepted: true,
        classification: result.classification,
        mutation_type: result.mutationType,
        l0_revision_event_hash_hex: bytesToHex(result.l0RevisionEventHash),
        l0_revision_node_type: found.nodeType,
        signer_public_key_hex: bytesToHex(signerPubkey),
        anchor_timestamp_unix_ns: wallClock.anchorTimestampUnixNs.toString(),
        anchor_nonce_hex: bytesToHex(nonceResult.nonce),
        ceremony_started_at_iso: startedAt,
        ceremony_completed_at_iso: completedAt,
      };
      // Genesis omits ceremony/chained_from; amendments place them right after
      // `mode` (matching the original hand-written field order).
      if (cfg.chainedFrom !== null) {
        return {
          mode,
          ceremony: cfg.ceremony,
          chained_from: cfg.chainedFrom,
          ...stripMode(base),
        };
      }
      return base;
    } finally {
      await client.shutdown();
    }
  } finally {
    if (ephemeral) {
      try { rmSync(opDir, { recursive: true, force: true }); } catch {}
      try { rmSync(stateDir, { recursive: true, force: true }); } catch {}
    }
    await killAllSpawnedHosts();
  }
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
 * The run_ceremony.ts CLI entry. Parses --mode, runs the ceremony, writes the
 * permanent off-chain ceremony_log record, prints the human summary to stderr
 * and the single-line JSON result to stdout. Exits 0 on accept, 1 on failure.
 */
export function cliRun(cfg: CeremonyConfig): void {
  const mode = parseMode();
  process.stderr.write(`[ceremony] mode=${mode} starting${cfg.startBannerSuffix}...\n`);

  runL0RevisionCeremony(cfg, mode)
    .then((res) => {
      const logPath = ceremonyLogPath(cfg, mode, res.ceremony_completed_at_iso);
      writeFileSync(logPath, JSON.stringify(res, null, 2) + "\n");
      process.stderr.write(
        `[ceremony] ACCEPTED\n` +
          `[ceremony] l0_revision_event_hash = ${res.l0_revision_event_hash_hex}\n` +
          `[ceremony] dag_node_type          = ${res.l0_revision_node_type}\n` +
          `[ceremony] signer_pubkey          = ${res.signer_public_key_hex}\n` +
          `[ceremony] log written to:        ${logPath}\n`,
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
