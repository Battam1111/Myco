# r/LocalLLaMA post draft

## Title

```
Built a substrate-style memory layer for agents — 18 verbs, self-validating, works with any local or hosted LLM via MCP
```

## Body

```
Posting because r/LocalLLaMA has seen a lot of "agent memory" solutions come through and I think this one differs from the others in ways that might interest you.

Myco (https://github.com/Battam1111/Myco) is a long-lived filesystem shape that an LLM agent maintains on your behalf. It's not a framework, not a vector DB, not a managed API. It's a directory of markdown notes + a YAML canon + a 25-dim lint system + an 18-verb CLI/MCP surface, designed so one agent can ingest, digest, cross-reference, and reshape the substrate across months without you babysitting it.

What distinguishes it from what's already been discussed here:

- **Provider-agnostic by design.** MP1/MP2 dimensions mechanically forbid the Myco kernel (and substrate-local plugins) from importing any LLM provider SDK. Your local llama.cpp, your Ollama, your Anthropic, your Groq — they all work because the substrate doesn't know which one you use. Your agent does.

- **No vector DB required.** The mycelium graph is built from AST import edges + markdown links + YAML `references:` fields — i.e. explicit cross-references the agent writes, not embeddings. That means the graph is inspectable + deterministic; no "why did retrieval miss that?" debugging.

- **Editable by default.** The install path clones the repo + `pip install -e`s it. The kernel IS a substrate (eats its own dogfood). You + your agent can molt the contract when the work outgrows the current shape.

- **10 MCP hosts supported.** Claude Code, Claude Desktop, Cursor, Windsurf, Zed, VS Code, OpenClaw, Codex CLI, Gemini CLI, Goose — one `myco-install` command configures them. MCP tool responses carry a pulse sidecar that echoes the R1-R7 rules to the agent on every call.

- **0 findings baseline.** v0.5.9 + v0.5.10 got the self-substrate's immune lint to 0 findings. Every new finding on myco-self is real signal, not noise. This matters because agents learn to skim noisy linters.

Quick start if you want to poke:

```bash
pipx run --spec 'myco[mcp]' myco-install fresh ~/myco-sandbox
cd ~/myco-sandbox
python -m myco hunger
python -m myco eat --content "testing this out"
```

Would love feedback on the architecture. The doctrine tree lives at [docs/architecture/](https://github.com/Battam1111/Myco/tree/main/docs/architecture) — L0 (five root principles) + L1 (R1-R7 rules) take ten minutes to read and answer most first-pass questions.

PyPI: https://pypi.org/project/myco/
MIT-licensed, Python 3.10+.
```

---

## Why this shape

- **Title names the differentiators up front.** "substrate-style",
  "18 verbs", "self-validating", "any local or hosted LLM" —
  each is a keyword r/LocalLLaMA cares about. "Memory" alone is
  too generic; a visitor needs the title to tell them why this
  post is different from the last 12 memory posts.

- **First paragraph acknowledges the audience has seen
  competitors** — no "revolutionary" language. r/LocalLLaMA
  rewards humility.

- **Four bullet points, each specific.** "Provider-agnostic by
  design" + "no vector DB required" + "editable by default" + "10
  MCP hosts" are the four angles that differentiate Myco from
  Mem0 / MemGPT / Letta / LangChain memory. Don't pad with a
  fifth.

- **"0 findings baseline"** is concrete + technical + signals
  discipline. r/LocalLLaMA trusts numbers over adjectives.

- **Quick-start block has real commands** that work end-to-end.
  A reader who copy-pastes should get from zero to running
  substrate in 30 seconds.

- **Doctrine callout at the end** — "L0 + L1 take ten minutes to
  read and answer most first-pass questions" tells readers the
  project has a thought-out shape, not "a weekend hack".

## What NOT to do

- **Don't mention Claude specifically in the title.** r/LocalLLaMA
  is distrustful of hosted-LLM marketing. MCP + Claude Code are
  fine in the body; the title should stay provider-neutral.
- **Don't post images/GIFs.** r/LocalLLaMA's top posts are text;
  images suggest marketing.
- **Don't auto-post at peak US time.** The subreddit's best
  engagement is 10am-2pm ET weekdays, but your submission will
  bob against whatever new benchmark / model-release post hit
  that hour. Post at 7-8am ET for longest visibility.

## After posting

Answer comments within the first 3 hours if you can. r/LocalLLaMA
rewards active OPs with sustained visibility; lurking OPs drop
fast.

Common first-comment shapes:

- "Looks like LangChain memory with extra steps" → the
  comparison is covered in the HN FAQ; lift that response.
- "How's this different from MemGPT?" → same, lift from HN FAQ.
- "Cool, but I already have Obsidian" → acknowledge Obsidian
  is great for human readers; Myco is for agent readers.
  Different target; no need to argue superiority.
