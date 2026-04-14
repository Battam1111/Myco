---
type: craft
status: ACTIVE
created: 2026-04-14
target_confidence: 0.85
current_confidence: 0.60
rounds: 3
craft_protocol_version: 1
decision_class: instance_contract
---

# Biomimetic Naming Audit & Reclassification

## Context

Myco's core aesthetic: every name should belong to a living mycelium organism.
eat/digest/forage/hunger/reflect/immune/scent/sense/metabolize/nutrient/hyphae/spore/fruit/decay/symbiont/graft.

User directive: "所有Myco的工具名也好其他名也罢，都尽可能贴合或使用仿生学词语。"

---

## Round 1: Bionic Lexicon & Deficit

### Already Bionic (Canon)
- eat, digest, condense, expand, prune, forage, absorb
- hunger, reflect, immune, sense, scent, observe
- mycelium, colony, graft, genome, propagate
- nutrient, substrate, hyphae, symbiont, autopoiesis, decay, excreted, metabolic, absorption, inlet

### Neutral-Engineering Candidates

| Name | Module | Tier | Alt | Rationale |
|------|--------|------|-----|-----------|
| first_run.py | bootstrap | A | germinate.py | Internal, seed→sprout metaphor |
| bootstrap.py | bootstrap | A | inoculate.py | Internal, inject-culture metaphor |
| hosts/ | integration | C | adapters/ | Needs metaphor debate (host vs adapter) |
| doctor_cmd.py | diagnostic | B | vitals / keep | Clear enough, marginal rename win |
| diagnose_cmd.py | diagnostic | B | keep | Overlap with doctor, defer |
| io_utils.py | utility | A | osmosis.py | Membrane transport metaphor |

**Deficit size**: 40 py files total; ~20 bionic; ~8 Tier A candidates; ~3 Tier B; ~2 Tier C.

---

## Round 1.5: Self-Rebuttal

**Against aggressive renaming:**
1. **"germinate vs first_run?"** — first_run is instantly clear; germinate requires domain knowledge. But it's internal → no API breakage. Win for rename.
2. **"hosts is already bionic"** — True. But is it right? Tree-hosts-myco OR myco-adapts-to-host? Metaphor direction matters. Needs debate.
3. **"doctor is clear, why rename?"** — "doctor" is idiomatic. Renaming adds metaphor but shadows clarity. Keep.
4. **"_load_canon → _read_genome?"** — Used in 10+ places. Scope explosion for marginal win. Keep.

**Decision**: Execute Tier A, keep Tier B, defer Tier C.

---

## Round 2: Final Tier Revision

### Tier A (Execute Now)
1. `first_run.py` → `germinate.py` (internal, zero public API)
2. `bootstrap.py` → `inoculate.py` (internal, matches lifecycle: spore→inoculate→germinate)
3. Update all imports (grep+replace in cli.py, inoculate.py itself)

### Tier B (Keep As Is)
- `doctor_cmd.py`: Already clear. Rename not justified.
- `diagnose_cmd.py`: Overlap unresolved.

### Tier C (Propose Only, Defer)
1. `hosts/` → `adapters/`: Metaphor debate unresolved (host vs adapter frame).
2. Consolidate doctor+diagnose: Needs architecture review.

---

## Round 3: Reflection

What does this reveal?
1. **Metaphor depth**: Naming is not just decoration—it frames how users think about the system.
2. **Scope-win tradeoff**: Small changes compound. Clear rename boundaries help.
3. **Clarity IS metaphor**: Best names (eat, digest, forage) where biology is the interface, not ornament.

**Confidence**: 0.85 on Tier A (high). 0.60 on deferral logic (medium—debate is live).

---

## Approved Execution

1. Rename `first_run.py` → `germinate.py`
2. Rename `bootstrap.py` → `inoculate.py`
3. Update imports everywhere
4. Write docs/bionic_lexicon.md
5. Run pytest + myco immune
6. Append to log.md

