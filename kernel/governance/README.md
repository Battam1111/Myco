# myco-kernel-governance

Myco v0.9 — kernel/governance (Python) per L3/PACKAGE_MAP §5.

## Modules (M2 scope)

- `canonical_bytes`: canonical-bytes serializer (cross-language parity with
  Rust `kernel/shared` + the TypeScript operator `operators/claude`).
- `crypto`: Merkle hash + HMAC + Ed25519 signature verification
  (cross-language parity). v0.9 keyless: the Ed25519 primitives cover the
  substrate's own F24 keypair + federation peer auth, not an owner key.
- `classifier`: I2 classifier function + dimension table (L1/GOVERNANCE §1.2).
- `schema_evolution`: schema-evolution gating helpers.

**v0.9 owner-key removal**: the `attestation` (owner-attestation envelope) and
`owner_keys` (key rotation / succession / cooldown) modules were removed with
the owner-key + anchor surface. CI mutations are classified keyless; the CI
authority is the doctrine-repo PR review + the BLAKE3 drift gate.

### Deferred (M6+ per L1/GOVERNANCE)

The following module scopes are doctrinally specified but not yet
implemented here; they are deferred to a later milestone (M6+):

- `lifecycle` — genesis / dormancy / reproduction / mortality FSM
  (L1/GOVERNANCE §4).
- `federation` — peer attestation list + freshness + aggregate reattestation
  (L1/GOVERNANCE §5).
- `rollback` — failed-evolution rollback (L1/GOVERNANCE §6).

## Development

```bash
pip install -e .[dev]
pytest
mypy src
ruff check src tests
```
