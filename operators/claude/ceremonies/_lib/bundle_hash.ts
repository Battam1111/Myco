// Shared bundle-hash machinery for L0-revision ceremonies.
//
// This module is the single source of truth for the two hash mechanisms
// every L0-revision ceremony binds:
//
//   prior_l0_hash — the hash the new revision chains FROM. Two providers:
//     * priorFromGitSha256(commit, path) — SHA-256 of a file retrieved from
//       git history (genesis: the DRAFT 9 SEALED monolith @ e796451).
//     * priorFromPinnedHex(hex)          — a pinned hex string equal to a
//       prior ceremony's new_l0_hash (amendments chain off the last bundle).
//
//   new_l0_hash   — BLAKE3 of canonical-bytes Map<rel_path, file_bytes> over
//     every `.md` under docs/architecture/L0/, keyed by path relative to that
//     root, in canonical-bytes Map ordering (BTreeMap = sorted by UTF-8 byte
//     sequence of the key). computeNewL0Hash() below.
//
// Both hashes are stable: bit-identical reproduction from this module + the
// working tree + git history must match the pinned values in each ceremony's
// `manifest.json`. Drift = doctrine-integrity breach.
//
// `_lib/` sits at the SAME directory depth as each ceremony dir. The
// canonical-bytes import below resolves to the operator package's own
// `src/canonical/` module (relocated there in the v0.9 owner-key teardown when
// the `anchor/client` TS package was deleted). REPO_ROOT is derived from this
// file's __dirname with the `../../../..` ascent the ceremony files used.
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
} from "../../src/canonical/canonical_bytes.ts";

// ---------------------------------------------------------------------------
// Repo-root resolution.
// ---------------------------------------------------------------------------

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Absolute path of the Myco workspace root.
 *
 * `_lib/` is at `operators/claude/ceremonies/_lib/`, the same depth as each
 * ceremony directory (`operators/claude/ceremonies/<ceremony>/`). The four
 * `..` segments ascend `_lib → ceremonies → claude → operators → <repo>` —
 * byte-identical to the per-ceremony `REPO_ROOT` it replaces.
 */
export const REPO_ROOT = join(__dirname, "..", "..", "..", "..");

/** Workspace-relative path of the v3.1+ doctrine root (unchanged across ceremonies). */
export const NEW_L0_ROOT = "docs/architecture/L0";

// ---------------------------------------------------------------------------
// Hex helpers.
// ---------------------------------------------------------------------------

export function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

export function hexToBytes(hex: string): Uint8Array {
  if (hex.length % 2 !== 0) throw new Error(`hex length not even: ${hex.length}`);
  const out = new Uint8Array(hex.length / 2);
  for (let i = 0; i < out.length; i++) {
    out[i] = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
  }
  return out;
}

// ---------------------------------------------------------------------------
// Bundle enumeration — deterministic walk.
// ---------------------------------------------------------------------------

/**
 * Recursively collect every `.md` file under `dir`, returning paths relative
 * to `root`. Sort lexicographically (matches canonical-bytes Map ordering:
 * keys ordered by UTF-8 byte sequence). Path separators are normalized to
 * forward slashes — canonical encoding MUST be platform-independent (matches
 * the Rust/Python ordering).
 */
export function collectMarkdownFiles(dir: string, root: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    const st = statSync(full);
    if (st.isDirectory()) {
      out.push(...collectMarkdownFiles(full, root));
    } else if (st.isFile() && entry.endsWith(".md")) {
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
// new_l0_hash — BLAKE3 of canonical-bytes Map<path, content>.
// ---------------------------------------------------------------------------

export interface BundleFileDigest {
  path: string;
  byte_length: number;
  sha256_hex: string;
}

export interface NewL0Hash {
  hash: Uint8Array;
  hashHex: string;
  bundleFiles: BundleFileDigest[];
  canonicalBytesLength: number;
}

/**
 * Compute new_l0_hash by:
 *   1. Enumerating bundle files (sorted by relative path).
 *   2. Reading each file's raw bytes.
 *   3. Building a canonical-bytes Map { path: bytes }.
 *   4. Canonical-bytes encoding the Map (deterministic key ordering).
 *   5. BLAKE3 hashing the encoded bytes.
 *
 * Cross-language reproducibility: any implementation of canonical-bytes +
 * BLAKE3 + a directory walk that respects the same path-sort order MUST yield
 * the same 32-byte hash. This is the live L0 doctrine fingerprint.
 */
export function computeNewL0Hash(): NewL0Hash {
  const root = join(REPO_ROOT, NEW_L0_ROOT);
  const relPaths = getBundleFiles();
  const map = new Map<string, Value>();
  const fileDigest: BundleFileDigest[] = [];

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
// prior_l0_hash — two providers.
// ---------------------------------------------------------------------------

export interface PriorL0Hash {
  hash: Uint8Array;
  hashHex: string;
}

/** A function that yields the prior_l0_hash for a ceremony. */
export type PriorProvider = () => PriorL0Hash;

/**
 * Genesis prior provider: SHA-256 of a file retrieved from git history.
 *
 * Retrieves `git show <commit>:<path>` raw bytes and hashes them with SHA-256
 * (not BLAKE3 — matches the API doc-comment on `signL0Revision`'s
 * `priorL0Hash` parameter for the genesis transition). The extra `byteLength`
 * is surfaced because the genesis manifest records it.
 */
export function priorFromGitSha256(
  commit: string,
  path: string,
): () => PriorL0Hash & { byteLength: number } {
  return () => {
    const bytes = execSync(`git show ${commit}:${path}`, {
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
  };
}

/**
 * Amendment prior provider: a pinned hex string equal to the prior ceremony's
 * new_l0_hash. The amendment chains off the last sealed bundle hash.
 */
export function priorFromPinnedHex(hex: string): () => PriorL0Hash {
  return () => ({ hash: hexToBytes(hex), hashHex: hex });
}
