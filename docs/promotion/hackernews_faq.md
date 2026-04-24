# HN FAQ: pre-drafted responses to predictable comments

The HN comment section on a Show HN follows predictable shapes.
Having concise responses pre-drafted lets you reply in minutes
instead of writing during the attention spike.

Adjust tone to match specific phrasing of the comment you're
replying to; keep each response < 200 words.

---

## Category 1: "Isn't this just X?"

### "Isn't this just LangChain memory?"

> LangChain's memory helpers (ConversationBufferMemory,
> VectorStoreMemory, etc.) are single-session stores that hand
> relevant chunks back to a chain on each call. They're a retrieval
> layer.
>
> Myco is a long-lived, self-validating filesystem shape + a 25-dim
> lint surface + a governance loop the agent uses to mutate its own
> contract. No chain, no retrieval-on-each-call. The agent reads
> the substrate by traversal, not by embedding similarity.
>
> Different tool. If you want retrieval-for-one-turn, LangChain
> memory is fine. If you want a substrate that survives six months
> of use and grows with the work, Myco is the shape I haven't seen
> elsewhere.

### "Isn't this just MemGPT / Letta?"

> MemGPT (now Letta) pioneered the tiered-memory-for-LLMs idea:
> main context + archival storage + recall hooks. I read their
> paper before starting Myco.
>
> Where Myco diverges: (1) the governance surface. MemGPT has
> memories; Myco has memories + a contract that explicitly
> describes how memories may evolve, enforced by 25 lint dims.
> (2) The kernel itself is a substrate. Myco is editable by the
> agent that maintains it, not a library the agent imports. (3)
> No vector DB hard-coupling. Myco's graph is AST + markdown-link
> derived, not embedding-derived.
>
> Letta is the right pick for "give my LLM a long context window";
> Myco is for "give my agent a knowledge base it grows itself".

### "Isn't this just Mem0?"

> Mem0 is a managed memory API: you POST memories to their
> service, they vector-index, and GET them back on retrieval.
> Great if you want zero-config memory + can ship the data to
> their cloud.
>
> Myco is an on-disk shape you own entirely. No API, no cloud,
> no egress cost, no "can I still access my memories if the
> company pivots?". Different deployment model; pick on trust
> + locality.

### "Isn't this just a Notion / Obsidian / Logseq for agents?"

> Three differences. (1) Notion/Obsidian/Logseq are designed for
> human reading; Myco is designed for agent reading. Every
> surface is primary material for the agent, not rendered for a
> human. (2) They have no lint surface. A broken cross-reference
> is a UI issue, not a kernel finding. Myco's SE1 flags dangling
> refs mechanically. (3) Their governance is "the user edits
> freely"; Myco's governance is the craft + winnow + molt loop
> that the agent participates in.

---

## Category 2: "Why would an agent need all this?"

### "LLMs will solve memory with longer context windows"

> Maybe. Myco's L0 appendix acknowledges this as a "living bet":
> if a sufficiently capable future agent can hold a 1M-file
> substrate in context and act coherently without structured
> verbs, Myco's verb surface is scaffolding that smarter agents
> discard.
>
> The counter-wager is that `cp`/`mv`/`grep` survived IDEs
> because they're coordination grammar, not UI. Myco's verbs
> serve the same purpose: a shared vocabulary for agents
> coordinating WITH each other or WITH the human, not a UI for
> the human to operate.
>
> We revisit this bet at every MAJOR release. MINOR releases
> assume the verbs stay valuable.

### "Why not just prompt engineering + a text file?"

> That's literally what Myco started as. After six months of
> "just a text file" I had 80 MB of raw material and no way to
> tell which of the 200 decision notes were still consistent
> with each other. The lint surface + the graph traversal
> weren't optional; they emerged from the pain of the
> unstructured baseline.
>
> If your "text file" stays under 10 MB and one session reads
> it end-to-end, you don't need Myco. If either of those
> breaks, you might.

### "Why 19 verbs? Isn't that too many?"

> 18 agent-facing + 1 human-facing (`brief`). Grouped into six
> biological subsystems, each exposing 2 to 7 verbs. The count
> comes from the life-cycle metaphor (germination / ingestion /
> digestion / circulation / homeostasis / cycle), not from
> feature-creep.
>
> An agent that knows the six subsystems can derive the verb
> it needs without memorising the full list. That's the design
> target: agents learn the structure, not the enumeration.

---

## Category 3: "What's the catch?"

### "What happens when the agent makes bad edits?"

> Three layers of defence. (1) R6 write-surface enforcement:
> verbs can only write paths declared in `_canon.yaml`; anything
> else raises `WriteSurfaceViolation` (exit 3). (2) Atomic writes
> via `atomic_utf8_write`: a crash mid-edit can't leave a torn
> file. (3) Git history, same as any other project. If the agent
> corrupts content inside the surface, `git reset` is your last
> line of defence.

### "What if the agent infinite-loops on molt?"

> `molt` requires an explicit new contract version string; it
> can't self-trigger. The only way it fires is the operator
> invoking it (or an agent invoking it on the operator's behalf
> with explicit intent).

### "How much does this cost to run?"

> Myco itself is MIT-licensed software that runs wherever Python
> runs; no per-query cost, no infrastructure cost. The LLM
> inference cost is whatever you already pay your provider. Myco
> doesn't add API calls in the happy path. It's a filesystem
> shape + a CLI + an MCP server, all local.

---

## Category 4: Specific-feature probing

### "Show me the doctrine. How does it stay coherent across edits?"

> The top-level contract lives in five specific markdown files:
> `docs/architecture/L0_VISION.md` (5 root principles),
> `docs/architecture/L1_CONTRACT/protocol.md` (R1 through R7 rules),
> `L1_CONTRACT/canon_schema.md`, `L1_CONTRACT/exit_codes.md`,
> `L1_CONTRACT/versioning.md`.
>
> Edits to those files require (1) a three-round craft under
> `docs/primordia/`, (2) `myco winnow` gate-check on the craft's
> shape, (3) owner approval, (4) `myco molt --contract <new>` to
> bump the contract version + append to
> `docs/contract_changelog.md`. Four layers of ceremony for
> kernel changes; zero ceremony for substrate-internal L4
> edits.

### "What's the smallest usable substrate?"

> Five files + two directories. See
> `examples/minimal/` in the repo. A `_canon.yaml` + `MYCO.md`
> at root + empty `notes/` + empty `docs/` + a
> `.myco_state/autoseeded.txt` marker.

### "Who is actually using this in production?"

> Myco itself uses Myco (the kernel IS a substrate; see the
> `_canon.yaml` at the repo root). A few private substrates
> downstream of Myco-self exist but haven't gone public. The
> honest answer is "pre-adoption, early 2026; the primary
> operator + agent combo is me + my Claude Code instance".
> That's real usage, not production-scale usage. Make your
> adoption decision accordingly.
