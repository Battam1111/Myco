// v3.1.1.1-p03-descriptive-amendment — deterministic hash computation.
//
// This amendment ceremony chains FROM the v3.1.1 ceremony's `new_l0_hash`.
// The L0 bundle-hash chain (each = BLAKE3 of canonical-bytes
// Map<rel_path, file_bytes> over docs/architecture/L0/**/*.md at that point):
//
//   b1bec59a... (v3.1 bundle) → 798c047d... (v3.1.1 bundle) →
//   2c3ecff1... (v3.1.1.1 bundle — this one)
//
// Where:
//   prior_l0_hash = the v3.1.1 ceremony's new_l0_hash
//                 = 798c047d592730e20375429706bde1dea3f3da26394891a0a3055de004dff824
//
//   new_l0_hash   = BLAKE3 of canonical-bytes Map<rel_path, file_bytes>
//                   over docs/architecture/L0/**/*.md as of v3.1.1.1 commit
//                 = (computed below; pinned in manifest.json)
//
// Doctrine change in v3.1.1.1 (Sprint 6.D; see manifest.diff_summary):
//   - P03_resumable_evolution.md descriptive amendment (version 2.1 → 3):
//     §3.3 reframed from 'two-phase migration' to 'snapshot-rollback
//     semantics' to match the shipping schema_evolution.py implementation;
//     §10.4 NEW acknowledged-debt section records multi-cycle migration as
//     a planned (not-yet-shipped) enhancement. DEPOSIT (P03 §2) unchanged.
//   - Folded into the same bundle: Sprint 7.H (Layer D catechumenate
//     scaffolding) + Sprint 7.I (cross-reference path-drift cleanup).
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

/**
 * Prior L0 hash for the v3.1.1.1 descriptive-amendment ceremony.
 *
 * This is the v3.1.1 ceremony's new_l0_hash (pinned in
 * v3_1_1_mortality_refinement_and_charite/manifest.json). Chains the
 * v3.1.1.1 descriptive amendment (Sprint 6.D's P03 §3.3 reframe) FROM
 * the v3.1.1 mortality+charite amendment.
 *
 * Chain so far:
 *   e796451 (DRAFT 9) → 5eacf3e7... (v3.1) → b1bec59a... (v3.1) →
 *   798c047d... (v3.1.1) → (this) v3.1.1.1
 */
export const PRIOR_L0_HASH_HEX =
  "798c047d592730e20375429706bde1dea3f3da26394891a0a3055de004dff824";

/** Workspace-relative path of the v3.1 / v3.1.1 doctrine root (unchanged). */
export const NEW_L0_ROOT = "docs/architecture/L0";

/**
 * Diff summary stored verbatim in the signed envelope for v3.1.1. MUST match
 * manifest.json `diff_summary`. Changes to this string invalidate the
 * signature; bumping diff_summary requires a new ceremony.
 */
export const DIFF_SUMMARY =
  "L0 v3.1.1.1 descriptive amendment (Sprint 6.D + Sprint 7.I): " +
  "(Sprint 6.D) " +
  "P03_resumable_evolution.md amended (version 2.1 → 3) to align " +
  "doctrine with shipping behavior. Specific changes: " +
  "(1) §3.3 reframed from 'two-phase migration (L1/SCHEMA §1.3)' to " +
  "'snapshot-rollback semantics' — describes actual " +
  "kernel/governance/.../schema_evolution.py::apply_schema_diff " +
  "implementation (snapshot → apply → I3 validate → commit-or-restore " +
  "in one cycle). " +
  "(2) §4.3 cascading update from 'candidate alongside current; M " +
  "consecutive cycles' to 'single-cycle snapshot-rollback apply' with " +
  "reference to §10.4 acknowledged debt. " +
  "(3) §5.2 wording adjustment: 'MUST NOT apply schema mutations " +
  "without two-phase migration' → 'MUST NOT apply schema mutations " +
  "OUTSIDE the snapshot-rollback envelope'. " +
  "(4) §7.1 M1 misreading clarified to honor both shipping behavior " +
  "AND target M-cycle migration. " +
  "(5) §10.4 NEW 'Acknowledged debt — multi-cycle two-phase " +
  "migration' section added: describes shipping state, target " +
  "enhancement, 5-step migration path (kernel/schema/src/migration.rs " +
  "two_phase_commit types + substrate bookkeeping + classifier " +
  "extensions + operator surface + C64 anticipated). " +
  "(6) §12 structural_anchors: phantom " +
  "`kernel/schema/src/migration.rs::two_phase_commit` (file never " +
  "existed) replaced by actual " +
  "`kernel/governance/.../schema_evolution.py::apply_schema_diff`. " +
  "DEPOSIT (P03 §2) UNCHANGED — `first-class mutable + " +
  "rollback-protected` honored by both shipping snapshot-rollback " +
  "AND planned M-cycle migration. Descriptive-amend per META §7; " +
  "deposit_immutable: false on P03 permits this non-deposit refinement. " +
  "(Sprint 7.I) Cross-reference path-drift cleanup across L0 + L1 + L2 + " +
  "L3 + algorithms + diagrams docs: all `L0/cards/<NAME> §X.Y` references " +
  "updated to `L0/cards/<NAME>.md §X.Y` form per L0/README.md §" +
  "\"What's still missing\" item 5. 22 files touched, ~70 references " +
  "updated. No deposit changes. Pure housekeeping per META §7. " +
  "(Sprint 7.H) Layer D catechumenate scaffolding: TEMPLATE.md (META §6.1 " +
  "session form template) + HOW_TO_ADD_A_SESSION.md (practical workflow " +
  "guide for cultivator-A + successor candidate). Zero sessions count " +
  "toward F21 activation — these are infrastructure files, not " +
  "catechumenate sessions. " +
  "Sealed 2026-05-19 (Sprint 6.D commit af6ef3b + Sprint 7.B/7.D/7.H/7.I).";

// ---------------------------------------------------------------------------
// Repo-root resolution.
// ---------------------------------------------------------------------------

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/** Absolute path of the Myco workspace root. */
export const REPO_ROOT = join(__dirname, "..", "..", "..", "..");

// ---------------------------------------------------------------------------
// Bundle enumeration — deterministic walk (same as v3.1 ceremony).
// ---------------------------------------------------------------------------

function collectMarkdownFiles(dir: string, root: string): string[] {
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

export function getBundleFiles(): string[] {
  const root = join(REPO_ROOT, NEW_L0_ROOT);
  return collectMarkdownFiles(root, root);
}

// ---------------------------------------------------------------------------
// prior_l0_hash — pinned to v3.1's new_l0_hash.
// ---------------------------------------------------------------------------

export function getPriorL0Hash(): {
  hash: Uint8Array;
  hashHex: string;
} {
  const bytes = hexToBytes(PRIOR_L0_HASH_HEX);
  return { hash: bytes, hashHex: PRIOR_L0_HASH_HEX };
}

// ---------------------------------------------------------------------------
// new_l0_hash — BLAKE3 of canonical-bytes Map<path, content> (v3.1.1 bundle).
// ---------------------------------------------------------------------------

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

function hexToBytes(hex: string): Uint8Array {
  if (hex.length % 2 !== 0) throw new Error(`hex length not even: ${hex.length}`);
  const out = new Uint8Array(hex.length / 2);
  for (let i = 0; i < out.length; i++) {
    out[i] = parseInt(hex.slice(i * 2, i * 2 + 2), 16);
  }
  return out;
}

// ---------------------------------------------------------------------------
// CLI entry.
// ---------------------------------------------------------------------------

const invokedAsCli =
  process.argv[1] !== undefined && process.argv[1] === __filename;

if (invokedAsCli) {
  const prior = getPriorL0Hash();
  const next = computeNewL0Hash();

  const out = {
    schema_version: 1,
    ceremony: "v3.1.1.1-p03-descriptive-amendment",
    chained_from: "v3.1.1-mortality-refinement-and-charite",
    prior_l0: {
      source: "v3.1.1 ceremony new_l0_hash (pinned in v3_1_1_mortality_refinement_and_charite/manifest.json)",
      hash_hex: prior.hashHex,
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
