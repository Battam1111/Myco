# myco-kernel-tropism

Myco v0.9 — kernel/tropism (Python) per L3_PACKAGE_MAP §7.

The substrate's **positive dispatch form**: continuously-evolving appetite
gradient with substrate-initiated sporocarp emission at fruiting triggers.
Per L1_TROPISM, this is the active alternative to v0.8's verb dispatch.

## Modules (M3 scope)

- `appetite_axis` — AppetiteAxis schema + per-axis state + UpdateRule trait.
- `gradient` — GradientConfiguration: per-cycle advance over all axes.
- `sporocarp` — Sporocarp data structure + emission at fruiting triggers.

## Modules (M4 deferred)

- `delta_absorption` — operator-emitted delta → axis perturbation routing.
- `birth_period` — birth-period flag + maturity-attestation hook.
- `template_registry` — template_version_registry per L1_TROPISM §B1.

## Development

```bash
pip install -e .[dev]
pytest
```
