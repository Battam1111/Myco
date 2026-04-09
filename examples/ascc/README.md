# Example: Multi-Month Academic Research Project

Myco's first real-world deployment. A comprehensive academic research initiative that developed a novel approach in machine learning.

## Project Stats (after 8 days)

| Metric | Value |
|--------|-------|
| System size | 17,000+ lines across 80+ files |
| Wiki pages | 10 (entity×2, concept×3, operations×2, analysis×2, craft×1) |
| Debate records | 15+ rounds of 传統手藝 with online research |
| Procedures | 7 documented operational workflows (P-001 to P-007) |
| Lint dimensions | 9 (L0-L8), all PASS |
| Evolution engine | Gear 1-3 executed, Gear 4 pending |

## How Myco Was Applied

### Bootstrap History

```
Day 1: Single 949-line entry document (before Myco existed)
Day 2: Restructured into 4-layer knowledge architecture
Day 3: Added canonical values file + automated consistency checking
Day 5: Added knowledge quality mechanisms (W8-W12)
Day 7: First milestone retrospective + evolution engine activated
Day 8: System named "Myco", vision crystallized, framework extraction begun
```

### Key Learnings

1. **Documentation drift is the #1 friction source** — 40% of friction came from "changed content, forgot to update index". Mitigation: Wiki Creation Checklist (index-first protocol).

2. **Evolution engine needs deliberate activation** — Initial friction count was 0 at first Gear 3 review. Mitigation: Lower trigger thresholds ("almost made a mistake" counts).

3. **Organic growth beats pre-planning** — All 10 wiki pages were created on demand, none pre-planned. The system should grow from practice, not from architecture diagrams.

4. **Canonical values prevent drift** — Same metrics were recorded differently in 3 locations. Centralized canonical values + automated enforcement solved this.

5. **Debate records are immutable history** — Never edit them. Conclusions get compiled to wiki; the debate record preserves the full reasoning chain for future reference.

## Directory Structure

```
project-root/
├── MYCO.md                # ~200 lines, L1 index (entry point for knowledge system)
├── _canon.yaml            # Canonical values, configuration, pattern detection
├── log.md                 # 90+ timeline entries across 8 days
├── docs/
│   ├── WORKFLOW.md        # ~700 lines, W1-W12 + all protocols
│   ├── SESSION_PROTOCOL.md
│   ├── operational_narratives.md  # Detailed procedures
│   ├── reusable_system_design.md  # Abstracted system architecture
│   └── current/           # 17+ debate/decision records (immutable)
├── wiki/
│   ├── [entity pages]      # Domain-specific entities
│   ├── [concept pages]     # Theoretical framework
│   ├── [operations pages]  # Procedures and patterns
│   ├── [analysis pages]    # Results and findings
│   └── [craft pages]       # Methodology and techniques
├── scripts/               # Automation tools (lint, search, deployment, etc.)
├── paper/                 # Research output (LaTeX source)
├── src/                   # Core implementation
└── research/              # Experimental runners + analysis
```
