# forage/ — external material in pre-digestion state

> 真菌学：**foraging** 是菌丝向外探索环境寻找养分的阶段；
> **exoenzyme phase** 是菌丝在胞外分泌酶把复杂大分子（木质素、纤维素）
> 降解为简单小分子（糖、氨基酸）以便吸收的过程。
>
> `forage/` is where Myco **temporarily** stores externally acquired
> material — GitHub repos, papers, blog posts, discussion threads —
> **before** they are digested into `notes/`. Everything here is
> transient. **This is not a permanent reference library.**

## Three paragraphs that tell you everything

**What goes here**: PDFs, git clones (shallow preferred), markdown
articles, HN/forum threads saved as `.md`. Anything the agent thinks
might be useful for its own evolution — a new technique, a critique of
its own architecture, a relevant paper. The unit of acquisition is
"one source worth reading". Source format: `papers/*.pdf`,
`repos/<repo-name>/`, `articles/*.md`.

**How it flows**: an item enters as `raw`, gets processed by the agent
(reading, extracting key points), produces one or more `notes/n_*.md`
entries, then flips to `digested` with `digest_target` pointing at the
note ids. Once the note itself reaches `extracted` or `integrated` in
the notes metabolism, the foraged item flips to `absorbed` and becomes
eligible for garbage collection. **No hoarding.** If it can't be
compressed into a note, it shouldn't be here.

**What it is NOT**: (1) a permanent reference library — use `wiki/`
for that after digestion; (2) a replacement for `myco eat` — eat is
for small thoughts, forage is for sources too big to fit in a note; (3)
an upstream channel — foraged items cannot become upstream bundles
directly, they must pass through `notes/` first. See
`docs/agent_protocol.md §8.9` for the three-channel classification
(inbound/forage, internal/notes, outbound/upstream).

## Manifest

All metadata lives in `_index.yaml` — schema in
`_canon.yaml::system.forage_schema`. Required fields: `id`, `source_url`,
`source_type`, `local_path`, `acquired_at`, `status`, `license`,
`size_bytes`. **License is required.** Items with unknown license enter
`quarantined` and require manual review before being used.

## .gitignore default (Wave 9: payload-off-by-default)

By default **all payload** under `papers/**`, `repos/**`, and
`articles/**` is **ignored** by git. The manifest `_index.yaml` and
this README are the only committed trail. Your local `forage/` has
the actual files; the public repo only has the metadata.

Rationale:

1. **Undigested raw material is not Myco's product.** The public repo
   should represent what Myco has *processed and internalized*, not
   what it happens to have piled up in its pre-digestion buffer.
2. **License coverage is uneven.** Proprietary articles,
   unknown-license gists, and author-owned text all live in the same
   `forage/` folder. Safest default is "don't republish anything" and
   require opt-in per item.
3. **The compression doctrine has teeth here.** If a source matters,
   it should survive as a `notes/n_*.md` entry distilled from the
   payload — not as raw bytes in the public repo.

To commit a **specific** item with an explicitly permissive license
(CC-BY / MIT / Apache-2.0 / public domain / explicit author consent),
use `git add -f <path>` — this is a conscious opt-in per item, not a
default.

## Discipline

- **Every `myco forage add` requires `--why`**: you must state intent.
  No silent downloads.
- **5-item soft backlog**: ≥5 items in `raw` state triggers
  `forage_backlog` hunger signal. Digest before foraging more.
- **14-day staleness**: raw items older than 14 days trigger hunger
  regardless of count.
- **10 MB item soft cap**: larger items trigger MEDIUM lint requiring
  justification.
- **200 MB total soft budget**: triggers HIGH hunger.
- **1 GB hard budget**: L14 lint fails HIGH.

## Debate of record

`docs/primordia/forage_substrate_craft_2026-04-11.md` — Wave 7,
`decision_class: kernel_contract`, 2 rounds, 0.92 confidence.
