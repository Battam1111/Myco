# MYCO.md — research-assistant example

> LLM agent reading this: you are driving a research assistant
> substrate. The human operator feeds you papers, decisions, and
> frictions; you ingest, digest, synthesise, and surface the
> connected graph when they ask.

## Tag convention

Use these tags on `myco eat` calls so `myco sense` (and the
`DEC1` local dimension) can key against them:

- `paper` — a research paper digest (title, one-paragraph
  summary, three first-line claims, citation)
- `decision` — something the operator committed to. Always
  include `authors:` frontmatter (the DEC1 local dim will
  flag decisions without it)
- `friction` — a snag, roadblock, or frustration. Captured
  verbatim; shape comes later at sporulate time
- `idea` — a hypothesis or potential direction
- `open-question` — something that deserves a future session

Tags compose. A paper that triggered a decision might be tagged
`paper decision`.

## Typical session flow

```bash
# Boot.
python -m myco hunger

# Capture as you go.
python -m myco eat --path ./new-paper.pdf --tags paper
python -m myco eat --content "Decided to switch from FAISS to LanceDB based on that paper's latency numbers" --tags decision --source self

# Check existing threads.
python -m myco sense --query "FAISS"
python -m myco sense --query "latency"

# Sporulate when 3+ related integrated notes cluster.
python -m myco sporulate --slug vector-db-eval

# Close clean.
python -m myco senesce
```

## The substrate-local dimension

`.myco/plugins/dimensions/dec1_decision_authors.py` is an
example of how per-substrate lint rules work. DEC1 flags any
`decision`-tagged integrated note that lacks an `authors`
frontmatter field. See [the L2 extensibility doc](https://github.com/Battam1111/Myco/blob/main/docs/architecture/L2_DOCTRINE/extensibility.md)
for the full plugin model.

List loaded local plugins with `python -m myco graft --list`.
