// v3.1-stratigraphy transition — deterministic hash computation.
//
// Produces two 32-byte hashes that bind the L0 doctrine transition:
//
//   prior_l0_hash = SHA-256(git show e796451:docs/architecture/L0_VISION.md)
//                 = the exact bytes of the DRAFT 9 SEALED monolith.
//
//   new_l0_hash   = BLAKE3(canonical_bytes(
//                     Map<relative_path_str, file_contents_bytes>
//                   ))
//                 = the v3.1 doctrine bundle, deterministically encoded.
//
// The bundle includes every `.md` file under `docs/architecture/L0/`,
// keyed by the path relative to that root, in canonical-bytes Map
// ordering (BTreeMap = sorted by UTF-8 byte sequence of the key).
//
// Both hashes are stable: bit-identical reproduction from this script
// + the working tree + git history must match the pinned values in
// `manifest.json`. Drift = doctrine-integrity breach.
//
// Per L1/HARD_RULES C18 canonical_bytes_render_drift (CRITICAL).

import { execSync } from "node:child_process";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join, relative, sep } from "node:path";
import { fileURLToPath } from "node:url";

import { blake3 } from "@noble/hashes/blake3.js";
import { sha256 } from "@noble/hashes/sha2.js";

import {
  encode,
  type Value,
  CanonicalBytes,
} from "../../../../anchor/client/src/canonical_bytes.ts";

// ---------------------------------------------------------------------------
// Constants — pinned forever.
// ---------------------------------------------------------------------------

/** Commit hash of the prior monolithic L0 (DRAFT 9 SEALED, 2026-05-17). */
export const PRIOR_L0_COMMIT = "e796451";

/** Path-in-prior-commit of the monolithic L0 file. */
export const PRIOR_L0_PATH = "docs/architecture/L0_VISION.md";

/** Workspace-relative path of the v3.1 doctrine root. */
export const NEW_L0_ROOT = "docs/architecture/L0";

/**
 * Diff summary stored verbatim in the signed envelope. Must match
 * manifest.json `diff_summary`. Changes to this string invalidate the
 * signature; bumping diff_summary requires a new ceremony.
 */
export const DIFF_SUMMARY =
  "L0 v3.1-stratigraphy: DRAFT 9 SEALED monolith → 4-layer doctrine institution " +
  "(Layer A 27 cards + Layer B 50 chengyu + Layer C 49 canonical dilemmas + " +
  "Layer D catechumenate placeholder + META + PROVENANCE). 4 eternity-clause " +
  "cards (P01c, P06, P07, P09). Phase 1+2 11-stream research + 3 craft rounds " +
  "+ Phase 3 unknown-unknown hunt with 7 amendments. Sealed 2026-05-18.";

// ---------------------------------------------------------------------------
// Repo-root resolution.
// ---------------------------------------------------------------------------

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/** Absolute path of the Myco workspace root. */
export const REPO_ROOT = join(__dirname, "..", "..", "..", "..");

// ---------------------------------------------------------------------------
// Bundle enumeration — deterministic walk.
// ---------------------------------------------------------------------------

/**
 * Recursively collect every `.md` file under `dir`, returning paths
 * relative to `root`. Sort lexicographically (matches canonical-bytes
 * Map ordering: keys ordered by UTF-8 byte sequence).
 */
function collectMarkdownFiles(dir: string, root: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    const st = statSync(full);
    if (st.isDirectory()) {
      out.push(...collectMarkdownFiles(full, root));
    } else if (st.isFile() && entry.endsWith(".md")) {
      // Normalize path separators to forward slashes — canonical encoding
      // MUST be platform-independent (matches Rust/Python ordering).
      const rel = relative(root, full).split(sep).join("/");
      out.push(rel);
    }
  }
  return out.sort();
}

/** Return the sorted list of bundle file paths (relative to `<repo>/docs/architecture/L0/`). */
export function getBundleFiles(): string[] {
  const root = join(REPO_ROOT, NEW_L0_ROOT);
  return collectMarkdownFiles(root, root);
}

// ---------------------------------------------------------------------------
// prior_l0_hash — SHA-256 of L0_VISION.md @ e796451.
// ---------------------------------------------------------------------------

/**
 * Compute prior_l0_hash by retrieving the file from git history and
 * hashing the raw bytes. SHA-256 (not BLAKE3) — matches the API
 * doc-comment on `signL0Revision`'s `priorL0Hash` parameter.
 */
export function computePriorL0Hash(): {
  hash: Uint8Array;
  hashHex: string;
  byteLength: number;
} {
  const bytes = execSync(`git show ${PRIOR_L0_COMMIT}:${PRIOR_L0_PATH}`, {
    cwd: REPO_ROOT,
    encoding: "buffer",
    maxBuffer: 16 * 1024 * 1024,
  });
  const raw = new Uint8Array(bytes);
  const digest = sha256(raw);
  return {
    hash: digest,
    hashHex: bytesToHex(digest),
    byteLength: raw.length,
  };
}

// ---------------------------------------------------------------------------
// new_l0_hash — BLAKE3 of canonical-bytes Map<path, content>.
// ---------------------------------------------------------------------------

/**
 * Compute new_l0_hash by:
 *   1. Enumerating bundle files (sorted by relative path).
 *   2. Reading each file's raw bytes.
 *   3. Building a canonical-bytes Map { path: bytes }.
 *   4. Canonical-bytes encoding the Map (deterministic key ordering).
 *   5. BLAKE3 hashing the encoded bytes.
 *
 * Cross-language reproducibility: any implementation of canonical-bytes
 * + BLAKE3 + a directory walk that respects the same path-sort order
 * MUST yield the same 32-byte hash. This is the v3.1 doctrine fingerprint.
 */
export function computeNewL0Hash(): {
  hash: Uint8Array;
  hashHex: string;
  bundleFiles: { path: string; byte_length: number; sha256_hex: string }[];
  canonicalBytesLength: number;
} {
  const root = join(REPO_ROOT, NEW_L0_ROOT);
  const relPaths = getBundleFiles();
  const map = new Map<string, Value>();
  const fileDigest: { path: string; byte_length: number; sha256_hex: string }[] =
    [];

  for (const rel of relPaths) {
    const abs = join(root, rel);
    const raw = new Uint8Array(readFileSync(abs));
    map.set(rel, { type: "bytes", value: raw });
    fileDigest.push({
      path: rel,
      byte_length: raw.length,
      sha256_hex: bytesToHex(sha256(raw)),
    });
  }

  const canonical: Value = { type: "map", value: map };
  const encoded: CanonicalBytes = encode(canonical);
  const digest = blake3(encoded.bytes);

  return {
    hash: digest,
    hashHex: bytesToHex(digest),
    bundleFiles: fileDigest,
    canonicalBytesLength: encoded.length,
  };
}

// ---------------------------------------------------------------------------
// Helpers.
// ---------------------------------------------------------------------------

function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

// ---------------------------------------------------------------------------
// CLI entry — `npm run ceremony:v3_1:hashes`.
// ---------------------------------------------------------------------------

// CLI detection — works cross-platform. process.argv[1] is the absolute
// path of the entry script (matches __filename when invoked directly).
const invokedAsCli =
  process.argv[1] !== undefined && process.argv[1] === __filename;
if (invokedAsCli) {
  const prior = computePriorL0Hash();
  const next = computeNewL0Hash();

  // Single-line JSON output for machine consumption + multi-line for humans.
  const out = {
    schema_version: 1,
    ceremony: "v3.1-stratigraphy-transition",
    prior_l0: {
      commit: PRIOR_L0_COMMIT,
      path: PRIOR_L0_PATH,
      byte_length: prior.byteLength,
      sha256_hex: prior.hashHex,
    },
    new_l0: {
      root: NEW_L0_ROOT,
      bundle_files: next.bundleFiles,
      canonical_bytes_length: next.canonicalBytesLength,
      blake3_hex: next.hashHex,
    },
    diff_summary: DIFF_SUMMARY,
  };

  process.stdout.write(JSON.stringify(out, null, 2) + "\n");
}
