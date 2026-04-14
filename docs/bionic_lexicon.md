# Myco Bionic Lexicon

A glossary mapping all Myco terms to their biological inspiration. This page documents the hidden aesthetic: Myco is an organism, not a tool.

## Core Concepts

| Term | Biological Analog | Meaning | Example |
|------|------|---------|---------|
| **eat** | Phagocytosis, ingestion | Capture raw information atom. Zero processing, pure intake. | `myco_eat --content "..."`  |
| **digest** | Enzymatic breakdown, metabolism | Chemically transform raw nutrient. Extract signal from noise. | `myco_digest <note_id>` |
| **nutrient** | Glucose, amino acids, minerals | Extracted, absorbable knowledge chunk (1–3 sentences). The output of digestion. | Stored in wiki/ or MYCO.md |
| **absorb** | Membrane transport, active uptake | Integrate nutrient into organism's structure. Must pass selective membrane (write surface). | `myco_absorb --content "..." --absorption-site wiki/...` |
| **substrate** | Soil, mycelium network, growth medium | The knowledge base (notes/, wiki/, docs/). The physical support structure. | `/sessions/.../Myco/` directory |
| **hyphae** | Fungal filaments, nutrient highways | Internal document links and cross-references. The circulatory system. | `<!-- nutrient-from: n_xxx -->` |
| **mycelium** | Networked fungal cells, the organism itself | The full knowledge graph (nodes + edges). Topology of all relationships. | `myco_mycelium stats` |
| **spore** | Reproductive unit, dormant potential | A project instance or archived knowledge package ready to replicate. | `.myco_state/spores/` (future) |
| **colony** | Interconnected fungal organisms sharing mycelium | Cohort of notes with common tag/theme. Semantic clustering. | `myco_colony gaps` |
| **forage** | Search for food in environment | Active scavenging of external sources (papers, code, articles). Keep in external cache. | `myco_forage <source>` |
| **graft** | Splice healthy tissue, genetic transfer | Merge external knowledge into the organism. Or: attach to host system (IDE integration). | `myco_graft <source>` or `hosts/` |
| **propagate** | Reproduce, spread spores | Generate copies or derive tools from core organism. | `myco_propagate` |
| **genome** | DNA, organism's specification | The canonical rules, contracts, patterns (\_canon.yaml, Myco.md, design decisions). | `_canon.yaml::system.*` |
| **evolve** | Mutation + selection, adaptation | Self-improvement loop. Agent modifies behavior based on friction signals. | `myco_evolve` (Wave E3) |
| **decay** | Decomposition, entropy increase | Knowledge no longer referenced. Marked for excretion. | `status: excreted` in notes/n_*.md |
| **excreted** | Waste excretion | Deliberately removed from active organism because replaced/superseded/invalid. Not deleted (archival). | `notes/.excretions/` |
| **symbiont** / **symbiotic** | Organism in mutual benefit relationship | Agent + Myco as co-evolutionary pair. Neither survives alone. | `myco_hunger(execute=true)` |
| **autopoiesis** | Self-producing, self-maintaining system | Myco's ability to self-heal and auto-evolve without external intervention. | `myco_immune` lint loops |
| **hunger** | Metabolic signal, nutrient depletion | System detects needs (raw backlog, craft missing, compression ripe) and broadcasts them. | `myco_hunger` returns signals |
| **metabolism** | Energy conversion, chemical cycles | Seven-step pipeline: discover→evaluate→extract→integrate→compress→verify→excrete. | `src/myco/metabolism.py` |
| **inlet** | Membrane pore, selective entry point | Gate for external content absorption. Tracks provenance. | `--inlet <source>` parameter |
| **outlet** | Membrane exit, excretion point | Gate for dead knowledge ejection. Tracks reason. | `myco_prune --excrete-reason "..."` |
| **immunity** | Immune system, pathogen detection | 29-dimensional lint system (L0–L28). Detects structural corruption. | `myco_immune` (Agent Review hybrid) |
| **scent** | Chemical signal, pheromone | Search results from wiki/docs/notes. Attractant for Agent attention. | `myco_scent <query>` (Wave 55+) |
| **sense** | Perception, proprioception | Unified search across knowledge base. Organism's self-awareness. | `myco_sense <query>` |
| **observe** | Visual inspection, sensory awareness | Read-only view of notes/ state. Non-invasive introspection. | `myco_observe --status raw` |
| **reflect** | Self-awareness, metacognition | End-of-session introspection ritual. Surface friction/growth. | `myco_reflect` |
| **condition** | Homeostasis, vital signs | System health metrics (raw_count, compression_pressure, draft_drift, etc.). | `indicators` in MYCO.md |
| **permeability** | Selective membrane properties | Write surface: which paths are writable, which are protected. | `_canon.yaml::system.write_surface` |
| **perfusion** | Blood circulation, nutrient delivery | Knowledge directory broadcast to Agent each session. Ensures no organ starves. | `myco_pulse → perfusion` field |
| **synaptogenesis** | Neural connection formation, rewiring | Automatic cross-linking when new knowledge is absorbed. Prevents island isolation. | L24 lint (synaptogenesis) |
| **interconnection** | Nervous system integration, body-wide coordination | Cross-layer concept mapping (knowledge ↔ engineering ↔ document). | L25 lint (cross-layer) |

## Rename History (Tier A Execution, 2026-04-14)

| Old Name | New Name | Module | Rationale | Status |
|----------|----------|--------|-----------|--------|
| `first_run.py` | `germinate.py` | bootstrap | Seed→first sprout metaphor. Lifecycle: spore→inoculate→**germinate**. | ✅ EXECUTED |
| `bootstrap.py` | `inoculate.py` | bootstrap | Inject initial culture. Lifecycle: **inoculate**→germinate→growth. | ✅ EXECUTED |

## Deferred (Tier B & C)

| Name | Considered Alt | Reason for Deferral | Status |
|------|---------|-----------|--------|
| `doctor_cmd.py` | `vitals`, `pulse`, `heartbeat` | Already clear idiomatic term. Rename adds metaphor but shadows clarity. | 🟡 KEEP |
| `diagnose_cmd.py` | consolidate with doctor | Overlap unresolved. Needs architecture debate. | 🟡 KEEP |
| `hosts/` (directory) | `adapters/` | Metaphor direction debate: host (tree) vs adapter (Myco adapts to external system)? | 🟡 DEFER |

## Guidelines for Future Naming

When introducing new modules, functions, or concepts in Myco:

1. **Prefer biological analog over neutral-engineering**. If it's part of the organism's metabolism, use mycology/biology.
2. **Clarity ≥ Metaphor**. A name that is clear AND bionic (e.g., "eat", "digest") beats a name that is bionic but requires domain lookup.
3. **Consistency within lifecycle**. Seed→inoculate→germinate→grow is a coherent arc. Don't break it with a random unrelated metaphor.
4. **Public API matters**. User-facing CLI commands and MCP tool names should be immediately recognizable. Internal functions can be more poetic.
5. **Document the metaphor**. Add a line in docstrings explaining the biological analog, so future devs understand the design choice.

## Examples of Good Naming Decisions

✅ `myco_eat` — Simple, bionic, instantly understandable (all organisms eat).
✅ `myco_digest` — Biological, clear semantics (break down into components).
✅ `myco_forage` — Evocative, clear intent (search outside the organism).
✅ `germinate` — Poetic but clear (first sprout, new growth).
✅ `inoculate` — Technical but biological (introduce starter culture).

## Examples of Rejected Naming Decisions

❌ `osmosis.py` for `io_utils.py` — Overly technical. Most users don't think of file I/O as osmosis.
❌ `vitals` for `doctor` — Slightly cuter but less clear. "doctor" is already idiomatic.
❌ `adapters/` for `hosts/` — Metaphor direction debate. Needs framing first.

---

**Craft of Record**: `docs/current/biomimetic_naming_craft_2026-04-14.md`  
**Last Updated**: 2026-04-14
