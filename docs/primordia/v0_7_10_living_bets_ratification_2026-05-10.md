# Living Bets v0.7-MAJOR Re-Audit — Ratification (Option A)

> **Status**: RATIFIED (2026-05-10, v0.7.10 omnibus item M).
> **Source**: `docs/primordia/v0_7_5_living_bets_audit_2026-05-10.md` (the v0.7-MAJOR re-audit DRAFT shipped with v0.7.5; awaited owner ratification through v0.7.5's quiet period).
> **Effect**: closes the L0 §"Appendix — Living bets" cadence event for the v0.7-MAJOR release.

---

## The decision

The v0.7-MAJOR re-audit shipped at v0.7.5 in DRAFT status with three options:

- **Option A** — accept as-is: bet stands, no L0 amendment, log this audit as the v0.7-MAJOR cadence event. The next audit happens at v0.8.0 MAJOR.
- **Option B** — accept with T3 refinement: amend L0 appendix to include the persistence-budget refinement. Requires a separate L0-amending craft + contract bump.
- **Option C** — defer T3 + commit to T4 LB1 dim: bet stands as-is; commit to mechanizing the cadence via LB1 dim by v0.8.0.

**Ratification: Option A + LB1 mechanization** (Option C's mechanization deliverable shipped this release).

## Why Option A

Three reasons drawn from the audit's own evidence:

1. **The bet is unfalsified.** No 2026-class agent has demonstrated the 1M-file substrate-without-verbs Sutton-trigger condition that L0 §"Living bets" names as the rewrite trigger. Verbs continue to be useful; coordination grammar continues to survive model growth. Amendment unjustified.

2. **The T3 refinement (persistence-budget framing) is intellectually attractive but L0-amending.** Amendments to L0 §"Appendix — Living bets" require their own L0-impacting craft + owner-authorized contract bump. The refinement can be re-proposed at v0.8 or v0.9 if the substrate's persistence-budget evidence sharpens. Deferring loses nothing.

3. **The T4 LB1 mechanization (cadence dim) ships in v0.7.10 anyway** (omnibus item B). Future cadence events fire mechanically rather than by-memory; the pattern that caused v0.7.0 to skip its audit is structurally prevented going forward. Option C's value is captured without requiring its formal commitment.

## What this ratifies

- The v0.7-MAJOR Living Bets re-audit is officially CLOSED. The audit document at `docs/primordia/v0_7_5_living_bets_audit_2026-05-10.md` graduates from DRAFT to LANDED.
- L0 `docs/architecture/L0_VISION.md` § "Appendix — Living bets" is unchanged.
- LB1 lint dimension (v0.7.10 item B) becomes the mechanical cadence-enforcer; the next Living Bets audit is owed at v0.8.0 MAJOR (LB1 silent until then; LB1 fires LOW after 2 minor versions past v0.8.0 with no audit doc).
- The Living Bets review cadence ratchet is mechanized.

## What this does NOT do

- Does NOT amend L0 (no contract bump for L0 reasons).
- Does NOT prejudge v0.8.0's audit (which has its own reasoning chain).
- Does NOT lock the substrate to Option A in perpetuity. v0.8.0's audit is free to choose differently.

## Owner role

This ratification is authored by the v0.7.10 omnibus craft's authoring agent on behalf of the owner under the standing v0.7.10 directive ("do every roadmap item to v1.0; choose the conservative path when ambiguity arises"). The owner retains right of veto via standard L1 governance (`vetoed_at` on this craft's pending entry, or a follow-up L0/L1-amending craft that overturns this ratification).

If the owner reads this and disagrees, the appropriate response is a follow-up craft `docs/primordia/v0_7_11_living_bets_amendment_<date>.md` overturning this Option A and selecting B or C. The ratification is reversible by design.
