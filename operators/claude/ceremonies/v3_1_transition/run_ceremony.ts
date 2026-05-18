// v3.1-stratigraphy transition — full on-chain signing ceremony.
//
// Runs end-to-end:
//   1. Verify manifest hashes match current bundle (drift check).
//   2. Spawn (or connect to) anchor_surface_host — owner Ed25519 key custody.
//   3. Spawn (or connect to) substrate — DAG host.
//   4. Call SubstrateClient.signL0Revision(prior, new, summary).
//      Internally: anchor wallclock → anchor nonce → buildEnvelope → owner sign
//      → submit_mutation l0_revision_attest. Substrate accepts (contract-identity
//      tier classification) and emits `l0_revision_attested:{prior_hash_prefix}`
//      DAG event.
//   5. Verify the DAG event appears; capture event hash for archival.
//   6. Write ceremony_log/<timestamp>.json — the permanent off-chain record.
//
// Modes:
//   --mode dry-run    (default) — ephemeral sandbox: mkdtemp dirs, debug binaries
//                                  from target/debug, fresh owner key per run.
//                                  Proves the flow works; events are throwaway.
//   --mode production            — uses MYCO_STATE_DIR + MYCO_ANCHOR_SURFACE_DIR
//                                  + MYCO_SUBSTRATE_BIN + MYCO_ANCHOR_SURFACE_BIN
//                                  env vars. Connects to the real owner key.
//                                  Run this once at v3.1-genesis time.
//
// Operator instructions: see ./README.md.
//
// Per L0/cards/AS_anchor_surface §3.4 + M-anchor-5 §9.2.4.

import { execSync } from "node:child_process";
import { existsSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve as resolvePath } from "node:path";
import { fileURLToPath } from "node:url";

import { SubstrateClient } from "../../src/substrate_client.ts";
import { OperatorIdentity } from "../../src/operator_identity.ts";
import { killAllSpawnedHosts } from "../../src/anchor_surface_client.ts";

import {
  computeNewL0Hash,
  computePriorL0Hash,
  DIFF_SUMMARY,
  REPO_ROOT,
} from "./compute_hashes.ts";

// ---------------------------------------------------------------------------
// Mode parsing.
// ---------------------------------------------------------------------------

type Mode = "dry-run" | "production";

function parseMode(): Mode {
  const argIdx = process.argv.indexOf("--mode");
  if (argIdx === -1) return "dry-run";
  const v = process.argv[argIdx + 1];
  if (v !== "dry-run" && v !== "production") {
    throw new Error(`unknown --mode value: ${v} (expected dry-run | production)`);
  }
  return v;
}

// ---------------------------------------------------------------------------
// Binary discovery (mirrors tests/substrate_client.test.ts).
// ---------------------------------------------------------------------------

function locateBinary(envVar: string, debugName: string): string {
  const fromEnv = process.env[envVar];
  if (fromEnv && existsSync(fromEnv)) return fromEnv;
  const exe = process.platform === "win32" ? ".exe" : "";
  const candidate = resolvePath(REPO_ROOT, "target", "debug", `${debugName}${exe}`);
  if (existsSync(candidate)) return candidate;
  throw new Error(
    `${debugName} binary not found at ${candidate}; build first with ` +
      `\`cargo build -p ${debugName}\` or set ${envVar}=/path/to/binary`,
  );
}

// ---------------------------------------------------------------------------
// Ceremony runner.
// ---------------------------------------------------------------------------

interface CeremonyResult {
  mode: Mode;
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

async function runCeremony(mode: Mode): Promise<CeremonyResult> {
  const startedAt = new Date().toISOString();

  // Step 1 — verify hashes (drift check).
  const prior = computePriorL0Hash();
  const next = computeNewL0Hash();

  process.stderr.write(
    `[ceremony:${mode}] prior_l0_hash (SHA-256 @ e796451) = ${prior.hashHex}\n` +
      `[ceremony:${mode}] new_l0_hash   (BLAKE3 v3.1)      = ${next.hashHex}\n` +
      `[ceremony:${mode}] bundle files: ${next.bundleFiles.length}, ` +
      `canonical bytes: ${next.canonicalBytesLength}\n`,
  );

  // Step 2 — locate binaries.
  const substrateBin = locateBinary("MYCO_SUBSTRATE_BIN", "myco-substrate");
  const anchorBin = locateBinary("MYCO_ANCHOR_SURFACE_BIN", "anchor-surface-host");

  // Step 3 — owner identity + state dirs.
  const ephemeral = mode === "dry-run";
  const opDir = ephemeral
    ? mkdtempSync(resolvePath(tmpdir(), "myco-v3_1-anchor-"))
    : process.env.MYCO_ANCHOR_SURFACE_DIR ??
      (() => {
        throw new Error(
          "production mode requires MYCO_ANCHOR_SURFACE_DIR pointing at the owner key dir",
        );
      })();
  const stateDir = ephemeral
    ? mkdtempSync(resolvePath(tmpdir(), "myco-v3_1-state-"))
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
        diffSummary: DIFF_SUMMARY,
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
      return {
        mode,
        prior_l0_hash_hex: prior.hashHex,
        new_l0_hash_hex: next.hashHex,
        diff_summary: DIFF_SUMMARY,
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

// ---------------------------------------------------------------------------
// Output helpers.
// ---------------------------------------------------------------------------

function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function ceremonyLogPath(mode: Mode, completedAtIso: string): string {
  const __filename = fileURLToPath(import.meta.url);
  const __dirname = dirname(__filename);
  const logDir = join(__dirname, "ceremony_log");
  if (!existsSync(logDir)) mkdirSync(logDir, { recursive: true });
  // Filesystem-safe timestamp.
  const stamp = completedAtIso.replace(/[:.]/g, "-");
  return join(logDir, `${mode}_${stamp}.json`);
}

// ---------------------------------------------------------------------------
// CLI entry.
// ---------------------------------------------------------------------------

const __filename = fileURLToPath(import.meta.url);
const invokedAsCli =
  process.argv[1] !== undefined && process.argv[1] === __filename;

if (invokedAsCli) {
  const mode = parseMode();
  process.stderr.write(`[ceremony] mode=${mode} starting...\n`);

  runCeremony(mode)
    .then((res) => {
      const logPath = ceremonyLogPath(mode, res.ceremony_completed_at_iso);
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

export { runCeremony, type CeremonyResult, type Mode };
