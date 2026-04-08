# Example: ASCC (Action Shaping in Continuous Control)

Myco's first real-world deployment. An academic research project targeting NeurIPS 2026.

## Project Stats (after 8 days)

| Metric | Value |
|--------|-------|
| System size | 17,000+ lines across 80+ files |
| Wiki pages | 10 (entity×2, concept×3, operations×2, analysis×2, craft×1) |
| Debate records | 15+ rounds of 传統手藝 with online research |
| Procedures | 7 (P-001 to P-007) |
| Lint dimensions | 9 (L0-L8), all PASS |
| Evolution engine | Gear 1-3 executed, Gear 4 pending |

## How ASCC Uses Myco

### Bootstrap History

```
Day 1: Single 949-line CLAUDE.md (before Myco existed)
Day 2: Restructured into 4-layer architecture
Day 3: Added _canon.yaml + lint_knowledge.py
Day 5: Added W8-W12 (knowledge quality mechanisms from Nuwa-Skill/Caveman)
Day 7: First Gear 3 retrospective + evolution engine activated
Day 8: System named "Myco", vision crystallized, framework extraction begun
```

### Key Learnings

1. **Documentation drift is the #1 friction source** — 40% of friction came from "changed content, forgot to update index". Mitigation: Wiki Creation Checklist (index-first protocol).

2. **Evolution engine needs deliberate activation** — Gear 1 friction count was 0 at first Gear 3 review. Mitigation: Lower trigger thresholds ("almost made a mistake" counts).

3. **Organic growth beats pre-planning** — All 10 wiki pages were created on demand, none pre-planned. The system should grow from practice, not from architecture diagrams.

4. **Canonical values prevent drift** — Same number (P4 progress) was once recorded differently in 3 locations. _canon.yaml + lint enforcement solved this.

5. **Debate records are immutable history** — Never edit them. Conclusions get compiled to wiki; the debate record preserves the full reasoning chain for future reference.

## Directory Structure

```
ASCC/
├── CLAUDE.md              # ~200 lines, L1 index
├── _canon.yaml            # Baselines, experiment config, stale patterns
├── log.md                 # 90+ timeline entries across 8 days
├── docs/
│   ├── WORKFLOW.md        # ~700 lines, W1-W12 + all protocols
│   ├── SESSION_PROTOCOL.md
│   ├── operational_narratives.md  # P-001 to P-007
│   ├── reusable_system_design.md  # → became Myco's architecture.md
│   └── current/           # 17+ debate/decision records
├── wiki/
│   ├── algorithms.md      # 12 algorithm variants
│   ├── environments.md    # 20 experiment environments
│   ├── theoretical_framework.md
│   ├── paper_strategy.md
│   ├── experiment_design.md
│   ├── results.md
│   ├── known_bugs.md      # BUG-1 to BUG-10
│   ├── ssh_hpc.md
│   ├── evolution_engine.md
│   └── paper_writing_craft.md
├── scripts/               # 17 scripts (deploy, test, lint, search, compress)
├── paper/                 # LaTeX source (17 pages, 0 errors)
├── src/                   # Algorithm implementations
└── research/              # Experiment runners + analysis pipeline
```
