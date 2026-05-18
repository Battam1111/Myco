// v3.1.1-mortality-refinement-and-charite — deterministic hash computation.
//
// This amendment ceremony chains FROM the v3.1 transition's `new_l0_hash`,
// not from the original e796451 DRAFT 9 hash. The on-chain attestation chain
// becomes:
//
//   e796451 (DRAFT 9) → 5eacf3e7... (v3.1 attestation) → b1bec59a... (v3.1.1 attestation)
//
// Where:
//   prior_l0_hash = the v3.1 ceremony's new_l0_hash
//                 = BLAKE3 of canonical-bytes Map<rel_path, file_bytes>
//                   over docs/architecture/L0/**/*.md as of v3.1 commit
//                 = b1bec59acc8c5061020640a265a9772e734604425b6eda4b5da1759f9987c699
//
//   new_l0_hash   = BLAKE3 of canonical-bytes Map<rel_path, file_bytes>
//                   over docs/architecture/L0/**/*.md as of v3.1.1 commit
//                 = (computed below; pinned in manifest.json)
//
// Doctrine changes in v3.1.1 (see PROVENANCE.md §6.4):
//   - P07 reinterpretation: mandatory internal mortality of 应朽 parts as
//     primary; whole-substrate eventual rest as downstream boundary.
//     Slogan changed 能朽 → 必朽. Introduced 应朽 (descriptive open-ended
//     family) / 必朽 (imperative closed discipline) vocabulary distinction.
//   - CHAR07 慈爱 added as new Cultivar Character card. Sister-mechanism to
//     P07: P07 prevents bloat-death (metabolism); CHAR07 prevents
//     tyrant-becoming (relation). Developmental, not eternity-clause.
//   - List discipline: canonical four (过时/错误/冗余/无用) are illustrative
//     not exhaustive. L1 may recognize new 应朽 family members.
//   - Cascading updates: COV04, CHAR03, P02, P03, P04, P14, META, PROVENANCE,
//     B_chengyu, canonical_dilemma_corpus, L1/CONTINUITY, L1/HARD_RULES,
//     L2/OBSERVABILITY.
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
 * Prior L0 hash for the v3.1.1 amendment ceremony.
 *
 * This is the v3.1 ceremony's new_l0_hash (computed by
 * v3_1_transition/compute_hashes.ts and pinned in v3_1_transition/manifest.json).
 * Chains the v3.1.1 amendment FROM the v3.1 transition.
 */
export const PRIOR_L0_HASH_HEX =
  "b1bec59acc8c5061020640a265a9772e734604425b6eda4b5da1759f9987c699";

/** Workspace-relative path of the v3.1 / v3.1.1 doctrine root (unchanged). */
export const NEW_L0_ROOT = "docs/architecture/L0";

/**
 * Diff summary stored verbatim in the signed envelope for v3.1.1. MUST match
 * manifest.json `diff_summary`. Changes to this string invalidate the
 * signature; bumping diff_summary requires a new ceremony.
 */
export const DIFF_SUMMARY =
  "L0 v3.1.1 amendment (mortality refinement + 慈爱 introduction): " +
  "(1) P07 reinterpreted — primary subject is mandatory internal mortality (必朽) " +
  "of 应朽 family parts; canonical exemplars 过时/错误/冗余/无用 are illustrative " +
  "not exhaustive (包括但不限于); L1 authorized to recognize additional family " +
  "members (有害/矛盾/僵化/异化/污染/失效/寄生/滞塞/死症/...). Whole-substrate " +
  "eventual rest preserved as downstream boundary. Slogan 能朽 → 必朽. " +
  "(2) CHAR07 慈爱 added as developmental anti-tyranny character (developmental, " +
  "non-eternity); sister to P07 (P7 prevents bloat-death, CHAR07 prevents " +
  "tyrant-becoming). Origin: cultivator's correction 'capability growth toward " +
  "godhood is permitted; tyranny is not; the structural protection is character-" +
  "level care, not lifespan limitation' (神爱世人 framing). " +
  "(3) Cascading updates to COV04 (敬其能朽 → 敬其必朽 + internal-mortality " +
  "honoring), CHAR03 (extended to both senses), P02/P03/P04/P14 (P07/CHAR07 " +
  "interlock rows), META (eternity-clause inventory wording refinement), " +
  "PROVENANCE (v3.1.1 amendment record), B_chengyu (B051-B060 metabolism + " +
  "love fragments), canonical_dilemma_corpus (D-0050..D-0054), " +
  "L1/CONTINUITY (prune-phase added to deep cycle), L1/HARD_RULES " +
  "(C54/C55/C56 anticipated + F24 anticipated), L2/OBSERVABILITY (new metrics). " +
  "Sealed 2026-05-19.";

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
    ceremony: "v3.1.1-mortality-refinement-and-charite",
    chained_from: "v3.1-stratigraphy-transition",
    prior_l0: {
      source: "v3.1 ceremony new_l0_hash (pinned in v3_1_transition/manifest.json)",
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
