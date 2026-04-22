# Minimal Myco substrate

The smallest possible working Myco substrate. Five files + two
directories. Everything an agent + `myco` verbs need to operate
against; nothing more.

## Tree

```
minimal/
├── README.md             you're reading it
├── _canon.yaml           substrate contract (identity, write_surface)
├── MYCO.md               agent entry page
├── docs/                 (starts empty; primordia land here when you fruit)
├── notes/                (starts empty; first `myco eat` populates raw/)
└── .myco_state/          runtime state (autoseeded.txt marker; gitignore candidate)
```

## Drive it

Open a terminal here and run:

```bash
# R1 — session boot ritual. Writes .myco_state/boot_brief.md.
python -m myco hunger

# Capture an insight.
python -m myco eat --content "the first thing I noticed is ..."
python -m myco eat --content "and here's a follow-up decision"

# Bulk-promote raw notes to integrated.
python -m myco assimilate

# Verify invariants.
python -m myco immune       # should exit 0

# R2 — clean session-end.
python -m myco senesce
```

After a couple of `eat + assimilate` cycles, `notes/integrated/`
will have promoted notes and `notes/distilled/` is ready for
`myco sporulate --slug some-theme` when you have multiple
related integrated notes to synthesise.

## Canon shape

```yaml
# _canon.yaml
schema_version: "1"
contract_version: "v0.5.10"
synced_contract_version: "v0.5.10"

identity:
  substrate_id: "minimal-example"
  tags: ["example"]
  entry_point: "MYCO.md"

system:
  write_surface:
    allowed:
      - "_canon.yaml"
      - "MYCO.md"
      - "notes/**"
      - "docs/**"
  hard_contract:
    rule_count: 7
  no_llm_in_substrate: true

subsystems:
  ingestion: {doc: "docs/architecture/L2_DOCTRINE/ingestion.md"}
  digestion: {doc: "docs/architecture/L2_DOCTRINE/digestion.md"}
  circulation: {doc: "docs/architecture/L2_DOCTRINE/circulation.md"}
  homeostasis: {doc: "docs/architecture/L2_DOCTRINE/homeostasis.md"}
  germination: {doc: "docs/architecture/L2_DOCTRINE/genesis.md"}
```

## Compare to `myco germinate`

`myco germinate --project-dir . --substrate-id minimal-example`
produces a roughly equivalent substrate from scratch. The only
meaningful difference is that this example carries a
pre-committed `docs/` + `notes/raw/` + `notes/integrated/`
directory structure with `.gitkeep` files, so `git clone` of an
example-containing repo doesn't lose the shape.

## Removing it

This directory is self-contained. `rm -rf examples/minimal`
removes all trace.
