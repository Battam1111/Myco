---
type: craft
topic: research_scope
slug: research_scope
kind: design
date: 2026-04-22
rounds: 3
craft_protocol_version: 1
status: APPROVED
---

# Research Scope — Craft

> **Date**: 2026-04-22
> **Layer**: L4 (this substrate's own operating rules; does not
> touch Myco kernel doctrine).
> **Governs**: how this research substrate uses the 18-verb
> surface.

---

## Round 1 — 主张 (claim)

Every research substrate forked from `examples/research-assistant/`
operates on the following claim: **the value of a long-running
research knowledge base is proportional to the connectedness of its
graph, not the volume of its notes**. Raw notes are cheap; orphans
accumulate cost forever. Therefore every `myco eat` in this
substrate MUST carry at least one tag from the canonical set
(`paper` / `decision` / `friction` / `idea` / `open-question`), and
every `decision` note MUST carry `authors` frontmatter.

## Round 1.5 — 自我反驳 (self-rebuttal)

- **T1**: Tag discipline is a principle-2 violation. L0 principle
  2 (永恒吞噬) says no filter on what enters. Requiring tags =
  filtering.
- **T2**: The `authors` requirement is duplicative — git history
  already tracks who committed. Adding a frontmatter field is a
  second source of truth.
- **T3**: This craft is L4-only (doesn't touch kernel doctrine),
  but substrate-local plugins CAN fail loud. DEC1 firing on every
  old decision note would flood immune with noise.

## Round 2 — 修正 (revision)

- **R1** (T1): Tag discipline isn't content-filtering — it's a
  metadata requirement. The raw content is unfiltered (any
  subject is welcome); only the tag is enforced. L0 principle 2
  speaks to "no filter on content"; tags are navigation aids,
  not content gates.
- **R2** (T2): Git history tracks the commit author, not the
  decision-maker. In a multi-agent or multi-operator substrate
  these diverge. The frontmatter `authors` field is the
  decision-maker; git records the scribe.
- **R3** (T3): DEC1 is LOW severity. It never gates CI. Noise on
  legacy content is expected; the signal is that new decisions
  should carry `authors`. The LOW severity is the designed
  compromise.

## Round 2.5 — 再驳 (counter-rebuttal)

- **T4** (re R1): "Tags are navigation, not gates" — but an
  `eat` call without a tag still succeeds. The "requirement" is
  social, not mechanical.

## Round 3 — 收敛 (convergence)

- **R4** (T4): Accepted. The requirement is convention enforced
  socially through this craft + through operator habit. A
  stricter mechanical check would require an MB-category local
  dimension that counts untagged raw notes and escalates past a
  threshold. Left as a v2 enhancement if convention proves
  insufficient in practice.

## Decision

Approved. Research-assistant substrates forked from this
template carry the tag + `authors` convention + the DEC1 local
dim as the load-bearing shape.

## Not in scope

- Kernel changes (those go upstream to
  [Myco's primordia](https://github.com/Battam1111/Myco/tree/main/docs/primordia)).
- A second or third local dimension — one is enough to
  demonstrate the axis.

## Why this matters (L0 tie-in)

- **Principle 5 (万物互联)**: tag discipline keeps the mycelium
  graph navigable. Untagged raw notes become orphans that SE1
  can't detect (they're not dangling — they're disconnected).
- **Principle 3 (永恒进化)**: the craft + molt loop applies to
  this substrate's own shape. If DEC1 proves insufficient, the
  next research-substrate fork updates this craft and lands a
  revised shape.
