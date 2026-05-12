---
proposed_doctrine: v-0-8-x-major-cycle-retrospective
sources:
- notes/integrated/n_20260510T172434Z_v0-8-0-living-bets-amendment-option-b-pe.md
- notes/integrated/n_20260510T172435Z_v0-8-0-major-omnibus-the-wager-refined-r.md
- notes/integrated/n_20260510T172436Z_v0-8-major-living-bets-re-audit-post-ame.md
distilled_at: '2026-05-10T17:24:50Z'
stage: distilled
ingest_state: distilled
synthesis_authored_at: '2026-05-11T17:30:00Z'
---

# Distillation: v0.8.x MAJOR Cycle Retrospective

> Synthesizes 3 v0.8.x crafts: the L0-amending Living Bets persistence-budget refinement (commit `783da78`), the v0.8.0 MAJOR omnibus that shipped 6 substantive items + L0 cascade review, and the v0.8.4 living bets re-audit that LB1 mechanically triggered at the v0.8 MAJOR boundary. Together they describe how Myco's first **modern-sense MAJOR release** unfolded.

## Three observations promoted from this cycle

### 1. **L0 amendments are tractable when L0 is well-isolated**

The v0.8.0 amendment to L0 § "Appendix — Living bets" cascaded to **zero** downstream documents. L1 contract (R1-R7) doesn't cite the wager. L2 doctrine (boundary, release_discipline, etc.) doesn't either. L3/L4 references the bet at high level only. A targeted L0 paragraph edit was a 200-line craft + ~25-line L0 diff, not a 2000-line refactor. **L0 isolation is the substrate's hidden affordance — built by the v0.4.x greenfield's strict layering, paid out at v0.8.0.**

### 2. **Amendment-as-craft + LB1 cadence enforcement = self-perpetuating governance**

The v0.7.5 P1 audit shipped LB1 dim. The v0.8.0 amendment cited the v0.7.5 audit as governance. The v0.8.4 audit shipped because LB1 fired. The cycle is **self-perpetuating** — the substrate's own lint dim now drives its own L0 review cadence. v0.7.0 missed its audit because cadence was honor-system; v0.8.0 + v0.9.0 + v1.0.0 cannot miss because LB1 fires LOW the moment MAJOR ticks past the most recent audit doc.

### 3. **First production federation is a half-realization that closes faster than expected**

v0.7.10's gap analysis flagged "no production federation peer" as the largest L0 P5 gap. v0.8.0 closed it in 5 minutes (germinate CC + add to federation_peers + run propagate end-to-end). The infrastructure cost was paid in v0.7.10 (3-peer fixture network + N-peer API). Closure was just a configuration moment. **Substrate work is back-loaded: the first 80% of capability takes 5 releases; the last 20% (production wire-up) takes 5 minutes.**

## Hotfix cadence honesty: v0.8.0 → v0.8.4 in 30 minutes

The v0.7.x distillation predicted "hotfix cadence is honest" (release_discipline.md Rule 4). v0.8.0 → v0.8.4 was the first production validation:

| Hotfix | Trigger | Lesson |
|---|---|---|
| v0.8.1 | CI ruff format check failed (3 files edited after format pass) | Local format check is necessary AND insufficient — must re-run after every late edit |
| v0.8.2 | CI test_image_ocr failed (no PIL) | Mock-test discipline must extend to fixture-construction, not just behavior assertions |
| v0.8.3 | CI test_propagate_collision_raises Python 3.11 only (xdist parallelism race) | Shared-fixture state under xdist is hazardous; per-test tmp clones are the safer default |
| v0.8.4 | CI cov-fail-under=85 missed (multimedia + OAuth added LOC; CI doesn't install heavy deps) | Coverage gate ≥ static threshold is brittle when extras are opt-in; floor must be graded against installed dep set |

**The post-hoc lesson** (added to release_discipline.md candidate list for v0.9): a v0.8.0-style ship should run a "CI matrix dogfood" locally — invoke `pytest -n auto --dist loadfile --cov-fail-under=85` against a fresh `pip install -e .[mcp,dev]` (matching CI's install scope) BEFORE pushing. Not the full-extras install (multimedia is opt-in by design) — exactly the dep set CI uses.

The owner's directive "不要疯狂迭代版本号了" (2026-05-11) is the operational consequence: future MAJOR releases should not waste 4 patch slots on routine CI debt. The substrate now operates under that discipline; subsequent engineering polish lands as commits-without-tags until enough accumulates to justify a meaningful version bump.

## Source notes (graph back-references)

- [v0_8_0_living_bets_amendment](../integrated/n_20260510T172434Z_v0-8-0-living-bets-amendment-option-b-pe.md)
- [v0_8_0_omnibus_craft](../integrated/n_20260510T172435Z_v0-8-0-major-omnibus-the-wager-refined-r.md)
- [v0_8_4_living_bets_audit](../integrated/n_20260510T172436Z_v0-8-major-living-bets-re-audit-post-ame.md)
