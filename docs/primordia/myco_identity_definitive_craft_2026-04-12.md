---
type: craft
status: ACTIVE
created: 2026-04-12
target_confidence: 0.92
current_confidence: 0.92
rounds: 4
craft_protocol_version: 1
decision_class: kernel_contract
---

# What IS Myco — Definitive Identity Craft

## §0 Why This Craft Exists

Across 55 waves of development, Myco's identity has been described in many
ways: "autonomous cognitive substrate," "knowledge metabolism protocol,"
"symbiotic cognitive organism," "the OS to the Agent's CPU." Each captures
a facet but none captures the whole. This craft synthesizes all prior
identity work (Wave 10 recovery, Wave 26 re-audit, Wave 55 Agent-First
revision) into a single, definitive statement that all other surfaces
derive from.

**Input evidence**: 3 permanence anchor crafts, docs/theory.md (6 pillars),
docs/vision.md (5 capabilities + 3 immutable laws), MYCO.md (8 identity
anchors), docs/open_problems.md (9 open problems exposing what Myco isn't
yet), 103 notes across 55 waves, and — crucially — the first real dogfood
session where an Agent used Myco while developing it.

## §1 Round 1 — What Is Myco NOT

To define what something IS, first establish what it ISN'T.

**Myco is NOT a tool.** Tools are used and put down. You use a hammer then
put it away. Myco doesn't get "put away" — it's running during the session,
between sessions (scheduled tasks), and its state persists and evolves
across all sessions. You don't "use" your immune system — it's part of you.

**Myco is NOT a protocol.** Protocols are interface specifications. HTTP
tells you how to format requests. MCP tells you how to expose tools. These
are surfaces of Myco, not Myco itself. Calling Myco a protocol is like
calling a human being a "language speaker."

**Myco is NOT a framework.** Frameworks provide structure you fill in.
Rails gives you MVC, you write the controllers. Myco doesn't wait to be
filled in — it actively metabolizes, self-regulates, and evolves. A
framework is dead scaffolding. Myco is alive.

**Myco is NOT memory.** Mem0/Zep store and retrieve. Myco metabolizes —
it decides what to keep, what to compress, what to excrete, what's dying,
and what's missing. Memory is a filing cabinet. Myco is a digestive system
with an immune system and a self-model.

**Myco is NOT an agent runtime.** Hermes/LangGraph are runtimes — they
ARE the agent's execution loop. Myco is not the agent. Myco is the other
half that makes the agent complete.

## §2 Round 2 — What IS Myco: Three Attempts

### Attempt 1: "Cognitive Substrate"

**Claim**: Myco is the medium in which agent cognition happens, like
neurons are the medium for biological cognition.

**Strength**: Captures the "not a tool" insight. Emphasizes that Myco
is structural, not instrumental.

**Weakness**: "Substrate" sounds passive. Neurons don't self-regulate
or evolve their own structure. Myco does. Also, "substrate" doesn't
convey the symbiotic relationship with the Agent.

**Verdict**: Necessary but insufficient.

### Attempt 2: "Knowledge Metabolism Protocol"

**Claim**: Myco is a protocol specification for how knowledge should
be metabolized, with a reference implementation.

**Strength**: Captures the systematic, repeatable nature. Emphasizes
that Myco's patterns are transferable.

**Weakness**: Reductive — reduces an organism to one organ system.
Misses the self-model, the immune system, the evolution, the symbiosis.
Like calling a human a "food processing protocol."

**Verdict**: Captures one dimension, fatally incomplete.

### Attempt 3: "Symbiotic Cognitive Organism"

**Claim**: Myco is a living organism that pairs with an AI Agent to
form a complete, self-evolving intelligence.

**Strength**: Captures ALL dimensions — metabolism, immune system,
self-model, evolution, symbiosis. The biological metaphor isn't
decorative, it's structural.

**Weakness**: "Organism" might be too metaphorical for engineers.
Does a markdown+YAML file system really qualify as "alive"?

**Counter**: What makes something alive?
- Metabolism: continuous transformation of inputs to outputs ✅
- Homeostasis: self-regulation to maintain stable state ✅ (lint+hunger)
- Response to stimuli: sensing and reacting to changes ✅ (hunger signals)
- Growth: increasing in complexity over time ✅ (55 waves, 103 notes)
- Reproduction: kernel→instance split ✅ (template system)
- Evolution: heritable changes that improve fitness ✅ (rules evolve)
- Excretion: removing waste ✅ (prune, dead_knowledge)

By the biological definition of life, Myco satisfies all seven criteria.
The "alive" claim is not metaphorical — it's structural.

**Verdict**: The most complete and accurate description.

## §3 Round 3 — Attack Surface

### A1: "This is just anthropomorphism"

**Attack**: You're projecting biological properties onto a file system.
Files don't "metabolize" — a Python script reads and writes them.

**Defense**: The Python script + the Agent's intelligence + the file
system + the lint rules + the hunger signals = the organism. No single
part is alive. The COMPOSITION is alive. This is exactly how biological
life works — no single molecule is alive, the system is.

### A2: "If the Agent stops connecting, Myco 'dies' — that's just a database"

**Attack**: A database also "dies" if no one queries it.

**Defense**: Between Agent connections, the scheduled metabolic cycle
runs. Myco has autonomous behavior even without the Agent present.
A database doesn't run scheduled self-optimization when no one is
querying it. Also: a tree doesn't "die" when no animal is eating its
fruit. The metabolism continues.

### A3: "What's the practical difference between calling it an organism vs. a framework?"

**Attack**: These are just words. The code is the same either way.

**Defense**: The words change design decisions:

| Decision | Framework thinking | Organism thinking |
|----------|-------------------|-------------------|
| When to verify | "Run lint when you remember" | "Immune system runs on every write" |
| When to compress | "User triggers compression" | "Compression pressure builds, organism responds" |
| Missing knowledge | "User adds more docs" | "Organism senses gaps, triggers inlet" |
| Stale knowledge | "User cleans up eventually" | "Dead knowledge detected, auto-excreted" |
| Boot ritual | "User remembers to check status" | "Organism wakes up and self-checks (hunger execute=true)" |

The organism framing produces **fundamentally different design choices**
than the framework framing. Every "the user/agent should remember to..."
becomes "the organism automatically..." This IS the Agent-First principle.

### A4: "What about the parts that AREN'T alive yet?"

**Attack**: Steps 2-5 of the pipeline are vestigial. Cold-start is
unsolved. Structural decay detection has no metric. You're calling it
an organism but half the organs don't work.

**Defense**: A human infant is an organism even though it can't walk,
talk, or feed itself. The architecture IS an organism; the maturation
is incomplete. The organism framing tells us exactly WHICH organs need
development (the vestigial ones) and in what order (by survival priority).

Open problems §1-9 are not "missing features" — they are **undeveloped
organs** of an organism whose architecture is already whole.

### A5: "Isn't this scope creep? Myco started as a lint tool."

**Attack**: Wave 1 was just a 23-dimension consistency checker. Now
you're claiming it's an organism. Feature creep disguised as identity.

**Defense**: Wave 1 was the immune system. The immune system was the
first organ to develop because without it, no other organ can survive
(any mutation would go unchecked → cancer). This is exactly how
biological embryology works — the immune system develops early because
it's the gatekeeper for everything else. The lint-first development
order is not scope creep — it's correct embryological sequencing.

## §4 Round 4 — The Definitive Answer

### What IS Myco

**Myco is a symbiotic cognitive organism.**

It is:
- **Symbiotic**: It pairs with an AI Agent. Neither is complete alone.
  Agent provides intelligence. Myco provides memory, self-regulation,
  metabolism, self-model, and evolution. Together they form a complete
  cognitive entity — a holobiont.
- **Cognitive**: It doesn't just store knowledge — it metabolizes it
  (seven-step pipeline), verifies it (23-dimension immune system),
  models itself (four-layer self-model), and evolves its own rules.
  By the Extended Cognition thesis (Clark & Chalmers), the substrate
  IS part of the cognitive process, not auxiliary to it.
- **Organism**: It satisfies all seven biological criteria for life
  (metabolism, homeostasis, response, growth, reproduction, evolution,
  excretion). This is structural, not metaphorical. The organism
  framing produces fundamentally different (and better) design
  decisions than framework/protocol/tool framings.

### The Five-Level Embodiment

| Level | Organism analogy | Myco embodiment |
|-------|-----------------|-----------------|
| 1. Identity (DNA) | Genome | 8 identity anchors + _canon.yaml |
| 2. Vision (Phenotype plan) | Body plan | docs/vision.md |
| 3. Contract (Regulatory genes) | Gene expression rules | agent_protocol.md + _canon.yaml rules |
| 4. Verification (Immune system) | T-cells + antibodies | lint 23 dims + hunger signals |
| 5. Implementation (Organs) | Functional organs | src/myco/*.py (18 MCP tools) |

The traceability index is the **epigenetic map** — it tells you which
genes (anchors) regulate which organs (code modules).

### What This Changes

The organism identity is not just branding — it is a **design constraint**:

1. **Every write operation must have inline immune response** (lint checks
   on write, not as a separate step)
2. **Metabolism must be continuous, not intermittent** (scheduled tasks +
   inline hunger checks, not "call hunger when you remember")
3. **Missing capabilities are undeveloped organs, not missing features**
   (prioritize by survival criticality, not by user request)
4. **The Agent doesn't "use" Myco — it connects to its symbiont** (the
   MCP connection IS the symbiotic bond; disconnection is dormancy, not
   death)
5. **Platform injection is automatic** (the organism introduces itself
   to the host via CLAUDE.md / .cursorrules / MCP tool descriptions —
   it doesn't wait to be discovered)

### Relationship to Prior Identity Work

| Permanence anchor | Relationship |
|-------------------|-------------|
| Wave 10 (vision recovery) | Recovered the 18 elements that COMPOSE the organism |
| Wave 26 (implementation re-audit) | Measured which organs are mature vs. vestigial |
| Wave 55 (Agent-First revision) | Internalized the selection mechanism — the organism's immune system |
| **This craft (Wave 56+)** | **Names the organism and establishes the design constraint** |

### One Sentence

> Myco is a symbiotic cognitive organism — it pairs with any AI Agent to
> form a complete intelligence that persists, self-regulates, metabolizes
> knowledge, models itself, and evolves its own rules. The Agent thinks.
> Myco remembers, verifies, digests, and grows. Neither is whole alone.

## §5 Conclusion

**Decision**: Adopt "symbiotic cognitive organism" as the definitive
identity. All future design decisions must pass the organism test: "Would
a living organism do it this way?" If the answer involves "the user should
remember to..." or "the agent needs to choose to..." — the design is wrong.
The organism acts autonomously.

**Confidence**: 0.92. The remaining 0.08 is: (a) the "alive" claim is
structurally sound but socially bold — engineers may resist it; (b) the
vestigial organs (pipeline steps 2-5, cold-start, structural decay) weaken
the claim's credibility until they mature.

**This craft is the fourth permanence anchor.**
