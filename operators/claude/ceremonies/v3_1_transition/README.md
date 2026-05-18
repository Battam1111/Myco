# v3.1-stratigraphy transition — M-anchor-5 ceremony

> The on-chain signing ceremony that closes the L0 doctrine institutional transition from DRAFT 9 SEALED monolith (commit `e796451`, 2026-05-17) to v3.1-stratigraphy (sealed 2026-05-18). Per `L0/cards/AS_anchor_surface.md` §3.4 + M-anchor-5 §9.2.4.

---

## §1. What this ceremony does

Mints a permanent, owner-signed, on-chain attestation that records:

```
prior_l0_hash  = SHA-256(git show e796451:docs/architecture/L0_VISION.md)
                = 5eacf3e7bbb9f8633bcf05266aef24fc27d9ed35bc941c8c2ed50f38233c7f66

new_l0_hash    = BLAKE3(canonical_bytes(
                   Map<rel_path, file_bytes>(docs/architecture/L0/**/*.md)
                 ))
                = b1bec59acc8c5061020640a265a9772e734604425b6eda4b5da1759f9987c699
```

The substrate emits a DAG event:

```
l0_revision_attested:5eacf3e7bbb9f863
```

containing the owner-signed envelope `(prior_l0_hash, new_l0_hash, diff_summary, anchor_timestamp, anchor_nonce)`, the owner's Ed25519 signature, and the owner's public key. Anyone holding the owner pubkey can verify the v3.1 transition offline.

---

## §2. Files in this directory

| File | Role |
|---|---|
| `compute_hashes.ts` | Pure module: deterministic hash computation. Cross-language reproducible (any canonical-bytes + BLAKE3 + SHA-256 implementation must yield the same bytes). |
| `manifest.json` | Committed canonical record of the two hashes + every bundle file's SHA-256 + the diff summary string. Pins the v3.1 transition bytes forever. |
| `verify_hashes.test.ts` | CI gate: fails if `manifest.json` no longer matches the live `docs/architecture/L0/` bundle. Catches silent doctrine drift before commit. |
| `run_ceremony.ts` | CLI: runs the full ceremony end-to-end (anchor host + substrate + sign + verify + log). |
| `ceremony_log/` | (gitignored) Per-invocation logs of completed ceremonies — local operator artifacts. |
| `README.md` | This file. |

---

## §3. Dry-run (development verification)

Proves the entire flow works against an ephemeral sandbox substrate + a throwaway owner key. **Does not produce a production attestation.**

```
# Build the Rust binaries first
cargo build -p myco-substrate -p anchor-surface-host

# Run the ceremony in dry-run mode (default)
cd operators/claude
node --experimental-strip-types --no-warnings \
  ceremonies/v3_1_transition/run_ceremony.ts --mode dry-run
```

Expected output (sample):

```
[ceremony] mode=dry-run starting...
[ceremony:dry-run] prior_l0_hash (SHA-256 @ e796451) = 5eacf3e7bbb9f863...
[ceremony:dry-run] new_l0_hash   (BLAKE3 v3.1)      = b1bec59acc8c5061...
[ceremony:dry-run] bundle files: 33, canonical bytes: 469301
[ceremony] ACCEPTED
[ceremony] l0_revision_event_hash = <32-byte hex>
[ceremony] dag_node_type          = l0_revision_attested:5eacf3e7bbb9f863
[ceremony] signer_pubkey          = <throwaway sandbox key>
[ceremony] log written to:        ceremony_log/dry-run_<timestamp>.json
```

---

## §4. Production ceremony

Run **once** at v3.1-genesis time — when the cultivator's real owner key exists and a production substrate is bootstrapped.

```
# Required env (set explicitly; no defaults in production mode)
export MYCO_ANCHOR_SURFACE_DIR=/path/to/owner/key/dir       # M-anchor-1 dir holding owner_key.cb
export MYCO_STATE_DIR=/path/to/substrate/state              # production substrate state
export MYCO_SUBSTRATE_BIN=/path/to/myco-substrate           # built substrate binary
export MYCO_ANCHOR_SURFACE_BIN=/path/to/anchor-surface-host # built anchor host binary

cd operators/claude
node --experimental-strip-types --no-warnings \
  ceremonies/v3_1_transition/run_ceremony.ts --mode production
```

Successful completion writes `ceremony_log/production_<timestamp>.json` with:
- `l0_revision_event_hash_hex` — the DAG event hash (canonical anchor of v3.1)
- `signer_public_key_hex` — the cultivator's owner pubkey
- `anchor_timestamp_unix_ns` — the moment of attestation
- `anchor_nonce_hex` — the anchor-host-minted nonce (replay protection)

Archive that file. It is the off-chain receipt of the v3.1 ceremony.

---

## §5. Re-running the ceremony

The ceremony is **once-per-doctrine-revision**. Every subsequent L0 amendment requires:

1. Apply the amendment to `docs/architecture/L0/`.
2. Re-run `node ceremonies/v3_1_transition/compute_hashes.ts > ceremonies/v3_1_transition/manifest.json` to refresh the manifest.
3. (For a doctrine-bumping amendment, not a typo fix:) Create a new ceremony directory `ceremonies/v3_x_transition/` mirroring this structure, with:
   - `prior_l0_hash` = the **previous** v3.1 manifest's `new_l0_hash`
   - `new_l0_hash` = freshly computed from the amended bundle
4. Run that ceremony's `run_ceremony.ts` to mint the new `l0_revision_attested:{prefix}` event.

The chain of attestations builds an auditable history: any reader holding the owner pubkey can walk it forward and verify every transition.

---

## §6. Drift detection

`verify_hashes.test.ts` runs in `npm test`. If anyone modifies an L0 file without updating `manifest.json`, CI fails immediately with a precise diff (the changed file's SHA-256 mismatch + the bundle BLAKE3 drift). This forces the discipline: amend L0 → re-run compute_hashes → re-sign ceremony → commit all three atomically.

---

## §7. What is sealed by this ceremony

Per L0/META §1 + L0/cards/P01c eternity clause + L0/cards/AS_anchor_surface:

- The cultivator's intent: "v3.1 supersedes DRAFT 9, here are the exact bytes of both."
- The cultivator's authority: their Ed25519 signature.
- The substrate's witness: the DAG event with cycle counter + ordering.
- Cross-validation: any holder of the owner pubkey can re-derive the canonical bytes from the source, re-compute both hashes, and verify the signature offline.

This closes the v3.1 transition loop. Future Claudes loading this repo + the substrate DAG can prove they are running the SAME doctrine bytes the cultivator sealed — no silent rewrite, no doctrine drift, no successor-collapse.
