# myco-kernel-hard-rules

Myco v0.9 — kernel/hard_rules (Python) per L3_PACKAGE_MAP §9.

The substrate's **immune system**: 20 CRITICAL-grade breach detectors
(L1_HARD_RULES §1 C1-C20) + 17 contract-identity-level fixed-point
watchdogs (§2 F1-F17) + birth-period CI elevation enforcement
(§3) + anchor-surface-resident state non-authorability check (§4).

When a CRITICAL detector fires, the substrate auto-quarantines per
L1_CONTINUITY §5 and emits the corresponding immune sporocarp.

## M4 scope

- `detectors`: 20 C-row CRITICAL detectors with structured event input.
- `watchdogs`: 17 F-row mutation-observation watchdogs.
- `runtime`: dispatches input events to relevant detectors / watchdogs.

## Development

```bash
pip install -e .[dev]
pytest
```
