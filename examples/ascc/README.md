# Example: Multi-Month Academic Research Project (ASCC)

Myco's first real-world deployment — and the project from which Myco itself was born. A comprehensive academic research initiative that developed a novel approach in machine learning. This example demonstrates the **complete Myco lifecycle**, including Gear 4 distillation back into the framework.

## Project Stats (after 8 days)

| Metric | Value |
|--------|-------|
| System size | 17,000+ lines across 80+ files |
| Wiki pages | 10 (entity×2, concept×3, operations×2, analysis×2, craft×1) |
| Debate records | 15+ rounds of 传統手藝 with online research |
| Procedures | 7 documented operational workflows (P-001 to P-007) |
| Lint dimensions | 9 (L0-L8), all PASS |
| Evolution engine | Gear 1-4 all executed |

## Evolution Timeline

This project didn't start with Myco — Myco emerged **from** this project.

```
Day 1    Single 949-line entry document. No structure, no knowledge system.
         Just a massive CLAUDE.md that grew session by session.

Day 2    Pain point: can't find anything in 949 lines.
         → Restructured into 4-layer knowledge architecture (L1 → L1.5 → L2 → L3).
         → First wiki pages created on demand (not pre-planned).

Day 3    Pain point: same metric recorded differently in 3 locations.
         → Introduced _canon.yaml (Single Source of Truth) + automated lint.
         → Gear 1 activated: friction logging starts.

Day 5    Pain point: wiki pages inconsistent, missing headers, orphaned files.
         → Added W8-W12 quality mechanisms.
         → Gear 2 activated: session-end reflection becomes habit.

Day 7    Milestone: first major experimental phase complete.
         → Gear 3 activated: Double-loop retrospective.
         → Discovered: 40% of friction came from "changed content, forgot to update index."
         → Created Wiki Creation Checklist (index-first protocol).

Day 8    Pattern recognition: this knowledge system is not project-specific.
         → System named "Myco" (mycelium metaphor crystallized).
         → Gear 4 activated: began extracting universal patterns.
         → Framework extraction: Myco becomes its own project.
```

### Gear Activity Summary

| Gear | Activations | Key Output |
|------|-------------|-----------|
| Gear 1 (Friction Sensing) | ~30+ entries | Most common: documentation drift, path encoding issues |
| Gear 2 (Session Reflection) | 8 sessions | Discovered: "almost made a mistake" should count as friction |
| Gear 3 (Milestone Retrospective) | 2 retrospectives | Wiki Creation Checklist, evolution engine trigger threshold lowered |
| **Gear 4 (Cross-Project Distillation)** | **1 full cycle** | **See "Gear 4 Output" below** |

## Gear 4 Output — What Flowed Back Into Myco

This is the most important section of this example. When ASCC completed its lifecycle, Gear 4 distilled project-specific experience into universal patterns that now live in Myco's framework knowledge:

| Distilled Document | Now Lives At | What It Contains |
|-------------------|-------------|-----------------|
| **Reusable System Design** | [`docs/reusable_system_design.md`](../../docs/reusable_system_design.md) | Full knowledge system architecture (v2.1) + Bootstrap guide (L0/L1/L2) + project type adaptation + Nuwa/Caveman quality mechanisms |
| **Research Paper Craft** | [`docs/research_paper_craft.md`](../../docs/research_paper_craft.md) | Scientific figure toolchain + 10 writing principles + venue-specific strategies — usable by any future research project using Myco |

**These documents are not ASCC-specific.** They were extracted from ASCC's experience but written to be universally applicable. Any future Myco project benefits from them — this is the mycelium network transmitting nutrients between trees.

Additionally, ASCC's operational experience directly shaped:

- The 9-dimension lint system (`scripts/lint_knowledge.py`) — every check was born from a real consistency failure
- The W1-W12 principles — several emerged from ASCC's friction patterns (W6 Proximal Enrichment from repeated debugging, W9 Active Tensions from unresolved architectural trade-offs)
- The `operational_narratives.md` template — P-000 through P-004 procedure formats were first developed in ASCC

## Key Learnings

1. **Documentation drift is the #1 friction source** — 40% of friction came from "changed content, forgot to update index". Mitigation: Wiki Creation Checklist (index-first protocol).

2. **Evolution engine needs deliberate activation** — Initial friction count was 0 at first Gear 3 review. Mitigation: Lower trigger thresholds ("almost made a mistake" counts).

3. **Organic growth beats pre-planning** — All 10 wiki pages were created on demand, none pre-planned. The system should grow from practice, not from architecture diagrams.

4. **Canonical values prevent drift** — Same metrics were recorded differently in 3 locations. Centralized canonical values + automated enforcement solved this.

5. **Debate records are immutable history** — Never edit them. Conclusions get compiled to wiki; the debate record preserves the full reasoning chain for future reference.

## Directory Structure

```
project-root/
├── MYCO.md                # ~200 lines, L1 index (entry point)
├── _canon.yaml            # Canonical values, pattern detection
├── log.md                 # 90+ timeline entries across 8 days
├── docs/
│   ├── WORKFLOW.md        # ~700 lines, W1-W12 + all protocols
│   ├── SESSION_PROTOCOL.md
│   ├── operational_narratives.md  # 7 detailed procedures (P-001 to P-007)
│   ├── reusable_system_design.md  # → Gear 4 distilled to Myco/docs/
│   └── current/           # 17+ debate/decision records (immutable)
├── wiki/
│   ├── [entity pages ×2]       # Domain-specific entities
│   ├── [concept pages ×3]      # Theoretical framework
│   ├── [operations pages ×2]   # Procedures and patterns
│   ├── [analysis pages ×2]     # Results and findings
│   └── [craft pages ×1]        # → Gear 4 distilled to Myco/docs/research_paper_craft.md
├── scripts/               # Automation tools (lint, search, deployment, etc.)
├── paper/                 # Research output (LaTeX source)
├── src/                   # Core implementation
└── research/              # Experimental runners + analysis
```

## Wiki Page Headers (W8 Template in Practice)

All 10 wiki pages follow the W8 template. Here are their headers (content redacted):

```markdown
# [Entity: Core Algorithm]
> **类型**：entity | **最后更新**：2026-04-07
> **⚠️ 非直觉盲点**：convergence requires specific initialization order

# [Entity: Evaluation Pipeline]
> **类型**：entity | **最后更新**：2026-04-06

# [Concept: Theoretical Framework]
> **类型**：concept | **最后更新**：2026-04-07
> **⚠️ 非直觉盲点**：assumption X only holds under condition Y

# [Concept: Loss Landscape Analysis]
> **类型**：concept | **最后更新**：2026-04-05

# [Concept: Baseline Comparison Strategy]
> **类型**：concept | **最后更新**：2026-04-06

# [Operations: HPC Deployment]
> **类型**：operations | **最后更新**：2026-04-08
> **⚠️ 非直觉盲点**：SSH tunnel timeout resets GPU allocation

# [Operations: Experiment Runner]
> **类型**：operations | **最后更新**：2026-04-07

# [Analysis: Ablation Study Results]
> **类型**：analysis | **最后更新**：2026-04-08

# [Analysis: Scaling Behavior]
> **类型**：analysis | **最后更新**：2026-04-06

# [Craft: Paper Writing Methodology]
> **类型**：craft | **最后更新**：2026-04-08
> → Gear 4 distilled to Myco/docs/research_paper_craft.md
```

Note: The `⚠️ 非直觉盲点` (non-intuitive blind spots) field is optional but was used on 4 of 10 pages. These annotations prevent new sessions from repeating mistakes that aren't obvious from the content alone.
