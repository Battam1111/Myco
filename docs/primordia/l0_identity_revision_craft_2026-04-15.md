# L0 Identity Revision — 2026-04-15

> **Status**: APPROVED by Yanjun on 2026-04-15, during greenfield rewrite.
> **Triggers**: contract-version bump at v0.4.0 release (will be recorded
> in `docs/contract_changelog.md`).
> **Supersedes**: the initial `L0_VISION.md` authored earlier this
> session (preserved in git history at commit 9bcbd19).

---

## Why a revision is needed

The initial L0 authored at 9bcbd19 contained two load-bearing statements
that Yanjun rejected:

1. **"Agent-first, human is the steward."** Too weak. Names the human as
   a role inside Myco's model. Yanjun: humans are NOT inside Myco's
   model. Myco is **Only For Agent — 人类无感知**. The human interacts
   with the agent and with the agent's outputs; Myco itself is invisible
   infrastructure for the agent. Human approval of contract changes is a
   *governance boundary*, not a routine surface.

2. **"Scoped to one project at a time. Multi-project federation is out
   of scope for v0.4."** Directly contradicts the whole point of a
   greenfield rewrite. Re-constrains v0.4 into the same single-project
   mold the old substrate outgrew. Myco must be a **general-purpose
   cognitive substrate** — project affiliation is a tag, not a boundary.

## Yanjun's replacement identity

Myco's root principles (宗旨), verbatim from the directive:

1. **Only For Agent**（人类无感知）
2. **永恒吞噬**（吞噬万物）
3. **永恒进化**
4. **永恒迭代**
5. **万物互联**（菌丝网络）

"其他所有实现都是围绕这若干点所延申的。" — every implementation detail
derives from these five.

## Round 1.5 self-rebuttal → Round 2 revision

**Objection A:** "人类无感知" literalized is false — the owner still
approves craft docs. **Resolution**: the approval surface is treated as a
*governance boundary*, not an interior surface. The substrate itself
(canon, notes, doctrine docs, code) exposes nothing to humans for
routine consumption. Craft-doc approval is a rare, explicit, gate-level
interaction — it does not make humans a "user" of Myco.

**Objection B:** "通用型知识库" risks dissolving into an undirected
dumping ground. **Resolution**: the five principles are themselves strong
constraints. 永恒吞噬 is not "accept anything as final" — it's "accept
anything as raw input, then digest." 万物互联 makes orphans fatal.
永恒进化 means the substrate's own shape is a first-class object that
reshapes over time. Generality is not formlessness.

**Objection C:** Do the seven L1 rules still hold? **Resolution**: the
rules are mechanics, not identity — they survive. Wording that assumes
a "project" or a "human user" will be patched; the rule count and
semantic intent are unchanged. See §Cascade Review below.

## Round 2.5 further rebuttal

**Objection D:** "Only For Agent" eliminates human-readable MYCO.md /
CLAUDE.md. Does that break downstream projects that expect those files?
**Resolution**: MYCO.md and CLAUDE.md stay — but their *audience* is
recast. They are agent-entry-point files. Their content is agent-facing.
A human can technically read them, but Myco does not optimize for that
experience, and human-readability is not a design constraint. This
aligns existing practice; only the framing changes.

**Objection E:** "通用型" means substrates can freely cross-federate. Does
that make `propagate` (cross-substrate push) the default rather than a
specialized operation? **Resolution**: propagate remains opt-in. Being
general-purpose means no artificial *ceiling* on federation, not that
federation is automatic. 万物互联 speaks to graph topology within and
across substrates; it does not mandate automatic bidirectional sync.

## Round 3 reflection

The initial L0 carried two residues of the pre-rewrite era — "steward"
framing (holdover from the docs adapter layer treating humans as a
first-class read audience) and "single project scope" (holdover from
ASCC being Myco's first and only downstream). Both were wrong defaults,
both caught early by Yanjun. This is exactly why the rewrite was
needed. Future L-layer drafts should be pressure-tested against the
five principles before landing.

## Cascade Review (which lower-layer docs need patching)

| File | What to patch | Why |
|------|--------------|-----|
| `docs/architecture/L0_VISION.md` | Full rewrite | Directly replaced by this revision |
| `docs/architecture/L1_CONTRACT/protocol.md` | R3/R4 wording: "project" → "substrate"; remove "human-readable" framing | Identity-layer consequence |
| `docs/architecture/L1_CONTRACT/canon_schema.md` | `identity.project` field: rename to `identity.substrate_id` (or similar); drop "one project" implication | Generality |
| `docs/architecture/L2_DOCTRINE/ingestion.md` | Emphasize 永恒吞噬 — no filter on intake | Identity-layer |
| `docs/architecture/L2_DOCTRINE/circulation.md` | 万物互联 framing for the mycelium graph; propagate as cross-substrate operation in a general-purpose network | Identity-layer |
| `docs/architecture/L2_DOCTRINE/digestion.md` | 永恒进化/迭代 framing — reflect/digest/distill are the engines of eternal iteration | Identity-layer |
| `docs/architecture/L2_DOCTRINE/homeostasis.md` | 永恒进化 does not exempt from invariants; immune system enforces form-under-evolution | Identity-layer |
| `docs/architecture/README.md` | Update reading order + L0 summary | Navigation |

No L3 changes required (package map and command manifest are
subsystem-agnostic).

## Approval

Yanjun, 2026-04-15: "MYCO的根本宗旨是：Only For Agent（人类无感知）、
永恒吞噬（吞噬万物）、永恒进化、永恒迭代、万物互联（菌丝网络），其他所有
实现都是围绕这若干点所延申的。必须是通用型知识库，我们都 greenfield
rewrite 了，不能够再被束缚。"
