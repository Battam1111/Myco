# myco-kernel-governance

Myco v0.9 — kernel/governance (Python) per L3/PACKAGE_MAP §5.

## Modules (M2 scope)

- `canonical_bytes` — canonical-bytes serializer (cross-language parity with
  Rust `kernel/shared` + TypeScript `anchor-client`).
- `crypto` — Merkle hash + HMAC + signature verification (cross-language
  parity).
- `classifier` — I2 classifier function + dimension table (L1/GOVERNANCE §1.2).
- `attestation` — attestation envelope construction + verification
  (L1/GOVERNANCE §2).
- `owner_keys` — key rotation + succession + cooldown window
  (L1/GOVERNANCE §3.1).
- `schema_evolution` — schema-evolution gating helpers.

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
