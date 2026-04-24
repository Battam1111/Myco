# dev.to / Medium long-form article draft

1500-2000 words. Technical deep-dive with concrete code blocks.
Suitable for dev.to (more developer-centric) or Medium (more
prose-friendly). Pick dev.to as primary; mirror to Medium if
you want.

---

## Title

```
Building Myco: a cognitive substrate for LLM agents whose kernel is editable by the agent that uses it
```

## Tags (dev.to max 4)

`ai`, `python`, `mcp`, `agents`

## Cover image

Use `assets/social_preview.png` (already in the repo). dev.to's
1000×420 constraint: check whether the social preview fits; if
not, use `assets/logo_dark_512.png` centered on a dark
background (any image editor + 30 seconds).

---

## Article body

```markdown
After six months of using LLM agents to maintain a long-running knowledge base, I hit a wall that wasn't about retrieval quality.

The problem wasn't that the agent couldn't find the right chunk. The problem was that the substrate (80 MB of notes, decisions, code snippets, and project histories) **contradicted itself**, and nobody noticed until a query returned three mutually-inconsistent facts.

This essay is about the tool I built to fix that: [Myco](https://github.com/Battam1111/Myco), a cognitive substrate for LLM agents whose kernel is editable by the agent that uses it.

## The design thesis

Most agent-memory tools optimise a retrieval metric: precision@k, chunk relevance, embedding recall, latency. That optimisation is real and valuable. Mem0, Letta, MemGPT, LangChain's memory helpers all do it well.

Myco optimises a different variable: **drift resistance under continuous edit**.

After six months of unstructured memory, the failure mode isn't "the agent couldn't find the thing". It's "the substrate contradicts itself and there's no mechanical check that catches the contradiction". The fix isn't better retrieval; it's a substrate that validates itself.

Three concrete examples of what "validates itself" looks like:

**1. Canon as single source of truth.** Every number, name, and path that matters (contract version, dimension roster, subsystem list, lint exit-code policy) lives in exactly one file: `_canon.yaml`. Other files reference this file by YAML `_ref`-suffixed fields; they never duplicate its values. A lint dimension (M1) fires when canon is missing required fields; another (SH1) fires when `__version__` in the Python package diverges from canon's declared version.

**2. Write-surface enforcement.** Every agent-writable path is declared in `_canon.yaml::system.write_surface.allowed` as an fnmatch-style glob. A dimension (M3) fires when the declaration is missing. At v0.5.8, this was strengthened from "lint catches writes outside the surface after the fact" to "verbs refuse to write outside the surface in the first place, raising `WriteSurfaceViolation` (exit 3)". Discipline-by-doctrine became discipline-by-mechanism.

**3. Graph connectedness.** The substrate is a graph: every node (canon field, note, doctrine page, code module) is reachable from every other by traversal. Edges come from four explicit sources (canon _ref fields, note frontmatter `references:` lists, markdown `[text](path)` links, AST import edges in Python modules). A dimension (SE1) fires per dangling edge; another (SE2) per orphan integrated note; another (SE3) per self-cycle.

25 dimensions total at v0.5.24. The full roster + fixability is in [L2 homeostasis.md](https://github.com/Battam1111/Myco/blob/main/docs/architecture/L2_DOCTRINE/homeostasis.md).

## The 19-verb surface

Every agent interaction with Myco goes through a verb. There are 19 total, grouped by biological subsystem:

```
germination   germinate
ingestion     hunger · eat · sense · forage · excrete
digestion     assimilate · digest · sporulate
circulation   traverse · propagate
homeostasis   immune
cycle         senesce · fruit · molt · winnow · ramify · graft · brief
```

All 19 are declared in [one YAML file](https://github.com/Battam1111/Myco/blob/main/src/myco/surface/manifest.yaml). The CLI (`python -m myco <verb>`) and the MCP tool server (via `myco.surface.mcp.build_server`) both derive from this file; there's no second registry to keep in sync.

A typical session looks like:

```bash
# R1: boot ritual
python -m myco hunger

# Capture as you go
python -m myco eat --content "decided to switch from FAISS to LanceDB after reading X paper" --tags decision
python -m myco eat --path ./paper.pdf --tags paper

# Check existing threads before writing code
python -m myco sense --query "vector database"

# Sporulate synthesis when you have 3+ related integrated notes
python -m myco sporulate --slug vector-db-eval

# R2: session end
python -m myco senesce
```

R1 and R2 are mechanically enforced: SessionStart / PreCompact / SessionEnd hooks in Claude Code (and compatible hosts) fire `hunger` and `senesce --quick` automatically. The agent doesn't forget; the host kills the process if it tries.

## The kernel IS a substrate

This is the design move I'm most proud of: Myco's own source tree is a substrate. The repo root has a `_canon.yaml`. The Python kernel code under `src/myco/` lives alongside `notes/` and `docs/` and is cross-referenced from the agent's mycelium graph.

Consequence: the agent that maintains Myco is the same agent a user would use to drive their own substrate.

Consequence²: `pip install myco` installs in editable mode by default (`pip install -e`). When the agent needs a new verb or a new lint dimension for its specific use case, it scaffolds one with `myco ramify --dimension NEW1 --category mechanical --severity low`. The scaffold lands under `src/myco/homeostasis/dimensions/new1_...py` (for kernel substrates) or under `.myco/plugins/dimensions/` (for downstream substrates).

The doctrine term for this is **永恒进化**, eternal evolution. The substrate's own shape is a first-class mutable object. Nothing in the kernel is "private API an agent must not touch".

## The governance loop

Kernel edits need governance, otherwise the eternal-evolution principle degrades into continuous drift. Three verbs compose the loop:

- `myco fruit --topic "some-slug"` scaffolds a three-round craft doc under `docs/primordia/` with the 主张, 自反, 修正, 再驳, 收敛 structure.
- `myco winnow --proposal docs/primordia/<file>` gates the craft's shape against a protocol (all five rounds present, not template boilerplate, frontmatter well-formed). Exit 1 if the shape fails.
- `myco molt --contract v<new>` mutates `_canon.yaml::contract_version` in lockstep with `synced_contract_version`, appends a section to `docs/contract_changelog.md`, and increments `waves.current`. Post-write validates by re-reading canon; rolls back on schema error.

v0.5.0 shipped on 2026-04-17. v0.5.24 shipped on 2026-04-24. 24 molts in one week, each with its own craft-doc trail at [docs/primordia/](https://github.com/Battam1111/Myco/tree/main/docs/primordia). The cadence is rapid because the substrate is young; the point is that *every* molt is visible, not silent.

## What's inside a lint dimension

Here's one of the newer dimensions as a concrete example:

```python
# src/myco/homeostasis/dimensions/cs1_contract_version_sync.py

class CS1ContractVersionSync(Dimension):
    """Canon's ``synced_contract_version`` matches ``contract_version``."""

    id = "CS1"
    category = Category.MECHANICAL
    default_severity = Severity.HIGH
    fixable: ClassVar[bool] = True

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        canon = ctx.substrate.canon
        if canon.synced_contract_version == canon.contract_version:
            return
        yield Finding(
            dimension_id=self.id,
            category=self.category,
            severity=self.default_severity,
            message=(
                f"canon.synced_contract_version "
                f"({canon.synced_contract_version!r}) differs from "
                f"canon.contract_version ({canon.contract_version!r})"
            ),
            path="_canon.yaml",
            fixable=True,
        )

    def fix(self, ctx: MycoContext, finding: Finding) -> dict[str, Any]:
        from myco.digestion.assimilate import _sync_contract_version
        changed = _sync_contract_version(ctx)
        return {
            "applied": changed,
            "detail": "updated canon.synced_contract_version" if changed else "already synced",
        }
```

One class per file. Registered via `[project.entry-points."myco.dimensions"]` in `pyproject.toml`. Third-party substrates add their own dimensions the same way, no fork of Myco required.

## What Myco is not

Being honest about limits keeps the expectations-reality gap small:

- **Not a framework.** Doesn't compete with LangChain, CrewAI, DSPy. Layer underneath; LangChain chains can call Myco's MCP tools.
- **Not a vector DB.** The graph is explicit-reference-based. If your use case needs embedding retrieval, add FAISS/LanceDB/Mem0 alongside Myco; they don't conflict.
- **Not a managed service.** All on-disk, MIT-licensed. Own your substrate.
- **Not production-battle-tested at scale.** Early 2026, pre-adoption. The primary user is me + my Claude Code instance on the Myco repo itself.

## Try it

```bash
pipx run --spec 'myco[mcp]' myco-install fresh ~/myco-sandbox
cd ~/myco-sandbox
python -m myco hunger
python -m myco eat --content "first insight from Myco"
python -m myco assimilate
python -m myco immune
```

Five commands, thirty seconds, and you have a working substrate. Ctrl+C out of it; `rm -rf ~/myco-sandbox` and nothing is left on disk.

If the shape interests you, the ten-minute read is:

1. [L0_VISION.md](https://github.com/Battam1111/Myco/blob/main/docs/architecture/L0_VISION.md): five root principles
2. [L1_CONTRACT/protocol.md](https://github.com/Battam1111/Myco/blob/main/docs/architecture/L1_CONTRACT/protocol.md): R1 through R7 rules
3. The [verb manifest](https://github.com/Battam1111/Myco/blob/main/src/myco/surface/manifest.yaml) for the 19-verb surface

Feedback on the architecture, especially on where the 25-dim lint surface is over-engineered or under-engineered for the drift-resistance target, is most welcome.

Repo: https://github.com/Battam1111/Myco
PyPI: https://pypi.org/project/myco/

MIT-licensed. Python 3.10+. 875 tests passing, 0 immune findings on the self-substrate at v0.5.24, A-tier on Glama's Tool Definition Quality rubric.
```

---

## Why this shape

- **1500-2000 words** hits dev.to's "full article" sweet spot:
  longer than a blog post, shorter than a whitepaper.
- **Opens with a concrete problem** (6 months, 80 MB, contradicting itself). Reader
  pattern-matches immediately.
- **"Design thesis" to "19-verb surface" to "The kernel IS a
  substrate" to "The governance loop" to "What's inside a lint
  dimension" to "What it is not" to "Try it"** structure lets
  readers drop out at any section with something useful.
- **Concrete code block** (CS1 dimension) turns an abstract
  "25 lint dims" claim into something the reader can point
  at.
- **"Try it"** section at the end with five working commands
  converts readers to users without friction.

## Posting notes

- Publish during US weekday morning; dev.to's algorithm
  favours engagement in the first 4 hours.
- Add the canonical URL if mirroring to Medium (dev.to gets rel=canonical,
  to keep SEO unified).
- Pick one cover image; dev.to articles without covers look
  unfinished.
