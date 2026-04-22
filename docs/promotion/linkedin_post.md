# LinkedIn post draft

LinkedIn is the most audience-mismatched of the channels here —
LinkedIn readers want business-context, not kernel-detail. Keep
the post short; link heavy lifting to the repo.

---

## Post body

```
Spent the last month building Myco — a long-term memory layer for LLM agents.

The problem: AI agents in Cursor, Claude Code, and similar tools have amnesia. Each session starts from zero. Across projects they re-derive the same conventions every morning. Six months of notes become an unsearchable text file.

The approach: treat agent memory as a **contract problem**, not a retrieval problem. A persistent filesystem + a 25-dimension lint system that catches when the substrate contradicts itself + a governance loop (fruit → winnow → molt) that lets the agent propose changes to its own contract instead of silently drifting.

What's shipped:
→ 18 manifest-driven verbs (CLI + MCP from one YAML)
→ 25 lint dimensions enforcing contract invariants mechanically
→ 10 MCP host integrations via one install command
→ 757 tests passing, 0 immune findings on the self-substrate
→ MIT-licensed, editable-default install

What it's not: a framework (doesn't compete with LangChain), a vector DB (graph is AST + markdown-link derived, not embedding-similarity), or a managed service (all on-disk, yours to own).

Most interesting technical bet: the kernel itself is a substrate. Myco eats its own dogfood — _canon.yaml at the repo root, doctrine in markdown the agent reads, the 25 lint dims running against the kernel on every commit. The agent that maintains Myco is the same agent a user would use to drive their own substrate.

Curious to hear from anyone running AI agents in production across long time horizons — what memory pattern has worked for you?

Repo: https://github.com/Battam1111/Myco
PyPI: https://pypi.org/project/myco/

(Tech-heavy, so linking the architecture doctrine for those who want to go deeper: https://github.com/Battam1111/Myco/tree/main/docs/architecture)
```

---

## Why this shape

- **Lead with the problem** (amnesia, re-derived conventions,
  unsearchable text). LinkedIn readers engage with
  pain-statement-first.
- **"Contract problem, not retrieval problem"** — the thesis
  line. LinkedIn posts need a quotable angle; this is it.
- **Four arrow-bulleted numbers** — LinkedIn's native format
  rewards arrow bullets over dashes visually.
- **Closing question** invites engagement without begging.
- **Three links** — repo + PyPI + docs. LinkedIn autolinks.

## When NOT to post this

If your LinkedIn network is non-technical, this will feel
alienating. Post only if your network has ≥ 10% ML / AI /
developer-tooling audience. Otherwise skip LinkedIn entirely;
it's not a strong-fit channel for infrastructure tools.

## Expected engagement

Low. LinkedIn doesn't surface GitHub links well in the feed
algorithm. The post's main value is as evergreen content on
your profile — someone who discovers you later and clicks
through sees a coherent "what is this person building" narrative.

Target: 50-200 views, 5-20 reactions, 2-5 comments in the
first week. If you hit those numbers, the post worked. Don't
compare to viral LinkedIn content; infrastructure tools don't
go viral on LinkedIn.
