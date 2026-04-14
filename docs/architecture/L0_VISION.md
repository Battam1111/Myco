# L0 — Vision

> **Status**: APPROVED (2026-04-15, greenfield rewrite §9).
> **Layer**: L0. Immutable unless explicitly revised by the project owner.
> **All lower layers (L1 Contract, L2 Doctrine, L3 Implementation, L4 Substrate) must conform to this page. In any conflict, L0 wins.**

---

## The one paragraph

**Myco is an agent-first symbiotic cognitive substrate for long-horizon
project work.** It exists so that an LLM agent collaborating with a human on
a single evolving project can enter every session with grounded,
project-specific context — decisions, constraints, open tensions, canonical
numbers — instead of re-deriving them from scratch. The agent is the primary
consumer; the human is the steward. Myco metabolizes raw inputs (notes,
decisions, debates) into structured, self-validating knowledge (canon,
digested notes, doctrine docs) and keeps that knowledge honest through an
immune system of lint checks. The substrate is alive: it grows, it digests,
it remembers, it self-audits, it dies gracefully.

## What Myco is not

- **Not a general-purpose knowledge base.** It is scoped to one project at a
  time. Multi-project federation is out of scope for v0.4.
- **Not a chatbot memory layer.** It is not optimized for conversational
  recall; it is optimized for *agent working context at session start*.
- **Not a documentation generator.** It does not author prose from
  templates. Humans and agents write; Myco metabolizes.
- **Not a replacement for version control.** Git owns history; Myco owns
  *current shape*.

## The three invariants

Every downstream decision must preserve these. If a proposed change breaks
one of them, the change is wrong — not the invariant.

1. **Agent-first consumption.** Every artifact Myco produces must be
   readable and usable by an LLM agent in a single session without extra
   tooling. Human readability is a bonus, not the primary target.

2. **Self-validating substrate.** Any claim Myco makes about the project
   (a number, a name, a path, a contract version) is checked by the immune
   system against a single source of truth. Drift is an error, not a
   warning.

3. **Stepwise refinement top-down.** The layering L0 → L1 → L2 → L3 → L4 is
   a strict subordination chain. A lower layer may specialize or implement
   an upper layer, but may never contradict or erode it. Implementation
   convenience is not a license to reshape the contract.

## Biological metaphor (authoritative)

Myco uses biological vocabulary deliberately and consistently. The metaphor
is not decoration — it names the load-bearing subsystems and their
relationships. L2 Doctrine formalizes each subsystem; L3 Implementation
mirrors the same names in code.

| Subsystem | Biological role | Cognitive role in Myco |
|-----------|-----------------|------------------------|
| **Genesis** | Seeding, birth | Bootstrap a fresh substrate skeleton |
| **Ingestion** | Feeding (eat, hunger, sense, forage) | Capture raw inputs and detect nutrient gaps |
| **Digestion** | Metabolism (reflect, digest, propagate) | Transform raw inputs into integrated structured knowledge |
| **Circulation** | Perfusion, signaling | Move information between subsystems; cross-reference graph |
| **Homeostasis** | Immune + regulation | Detect drift, enforce invariants, preserve identity |

Commands, subsystems, and directory names at every layer must match this
taxonomy exactly. No alternate vocabulary is permitted.

## Downward mapping (references only — full tables in each layer)

- **L1 Contract** (see `L1_CONTRACT/protocol.md`): encodes the three
  invariants as seven enforceable rules (R1–R7).
- **L2 Doctrine** (see `L2_DOCTRINE/`): specifies each subsystem's
  responsibility, boundary, and interface.
- **L3 Implementation** (see `L3_IMPLEMENTATION/package_map.md`): maps each
  subsystem to exactly one Python package under `src/myco/`.
- **L4 Substrate** (see `_canon.yaml`, `notes/`, `docs/`): the concrete
  instance — regenerated fresh at v0.4.0, not carried forward.

## Changes to this page

This page changes only when the project owner explicitly requests a
revision to Myco's identity. Such revisions require a new craft doc under
`docs/primordia/`, approval recorded in the craft, and a contract-version
bump. Editing L0 is never a routine or implementation-driven activity.
