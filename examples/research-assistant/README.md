# Research-assistant Myco substrate

A realistic starter substrate for a solo researcher, the use case
Myco was shaped around. This shows how the 19-verb surface + 25
dims support a long-running knowledge base of papers, decisions,
frictions, and synthesis.

Compared to [`../minimal/`](../minimal/), this example includes:

- **Pre-seeded** `notes/integrated/` with three example entries
  (a decision, a paper digest, a friction note) so `myco sense`
  returns hits out of the box.
- **Custom tag scheme** in `_canon.yaml::identity.tags`:
  `paper`, `decision`, `friction`, `idea`, `open-question`.
- **A wider `write_surface.allowed`** that includes
  `research/**` for domain-specific artefacts outside standard
  notes/.
- **A sample `docs/primordia/` craft** showing what a
  research-track three-round proposal looks like.
- **A `.myco/plugins/` demo**: one substrate-local dimension
  that checks every `decision`-tagged note has an `authors`
  frontmatter field. Demonstrates the extensibility axis.

## Shape

```
research-assistant/
├── README.md                              (this file)
├── _canon.yaml                            research-substrate contract
├── MYCO.md                                agent entry page
├── docs/
│   ├── architecture/                      (stub; crafts land here)
│   └── primordia/
│       └── research_scope_craft_2026-04-22.md
├── notes/
│   ├── raw/                               (empty; eat populates)
│   ├── integrated/
│   │   ├── n_20260422T100000Z_example-paper-digest.md
│   │   ├── n_20260422T100100Z_example-decision.md
│   │   └── n_20260422T100200Z_example-friction.md
│   └── distilled/                         (empty; sporulate populates)
├── research/                              user-owned domain artefacts
│   └── .gitkeep
└── .myco/
    └── plugins/
        ├── __init__.py
        └── dimensions/
            └── dec1_decision_authors.py   substrate-local dim
```

## Drive it

```bash
cd examples/research-assistant

# Boot.
python -m myco hunger

# Check the pre-seeded content.
python -m myco sense --query "decision"
python -m myco sense --query "paper"

# Add material.
python -m myco eat --content "Read Anthropic's 2026 long-context paper; key finding: cache invalidation semantics differ from OpenAI" --tags paper research
python -m myco eat --content "Decided to use Myco for the agent-memory layer; evaluated Mem0 + Letta + MemGPT" --tags decision
python -m myco assimilate

# Sporulate the emerging synthesis.
python -m myco sporulate --slug agent-memory-evaluation

# Lint: the substrate-local dimension DEC1 will run alongside the
# kernel's 25, checking that every `decision`-tagged note has an
# `authors` field.
python -m myco immune

# Observe the plugin.
python -m myco graft --list
```

## Extending

This substrate is a fork of the minimal template with:

1. **Added `research/**` to write_surface** so the agent can write
   domain-specific artefacts (plots, datasets, evaluation scripts).
2. **Added `paper` / `decision` / `friction` / `idea` /
   `open-question` to the canonical tag set.** These are not
   enforced by a dimension; they're convention for `myco sense`
   to key against.
3. **Added one substrate-local dimension DEC1**, a toy example
   of how `.myco/plugins/dimensions/` works.

## Adapting for yourself

Copy this directory to `~/my-research/` (or wherever), edit
`_canon.yaml::identity.substrate_id` to something unique, and
delete the pre-seeded `n_example-*.md` notes. You have a fresh
research substrate ready to feed.
