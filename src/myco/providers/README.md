# `src/myco/providers/` — declared LLM provider escape hatch

**Status at v0.5.7:** empty by design (invariant mechanically enforced since v0.5.6 via MP1).

## What this directory is

L0 principle 1 of the Myco contract says:

> Agents call LLMs; the substrate does not embed provider calls in its
> own logic.

At v0.5.6 that invariant became **mechanically enforced** by the MP1
immune dimension (`src/myco/homeostasis/dimensions/mp1_no_provider_imports.py`).
MP1 scans every `.py` file under `src/myco/` and emits a HIGH-severity
finding if any file imports a known LLM provider SDK
(`openai`, `anthropic`, `mistralai`, `cohere`, `voyageai`,
`google.generativeai`, `google.genai`, `langchain`, `langchain_core`,
`langchain_openai`, `langchain_anthropic`, `llama_index`, `llama_cpp`,
`ollama`).

This `providers/` directory is the **single, named, auditable
exception** to that rule. MP1 skips the entire `src/myco/providers/`
subtree. If a module lives here, MP1 will not complain about its
provider imports.

## Why the exemption exists

A rule without an escape hatch is either a rule people quietly
subvert or a rule that blocks legitimate work. Making the exception
**named** (`providers/`), **path-scoped** (not dimension-scoped),
and **canon-gated** (requires `no_llm_in_substrate: false`) means:

- Nobody can sneak a provider call into `ingestion/` or `digestion/`
  and pretend it was an honest mistake.
- A downstream reader of `_canon.yaml` can tell at a glance whether
  the substrate honors the agent-first boundary.
- The decision to accept provider coupling gets a real contract
  entry (via `myco molt`) instead of happening silently.

## What you must do to add a provider module

Adding any concrete module under `src/myco/providers/` requires
**all three** of the following, in order:

1. **Set `canon.system.no_llm_in_substrate: false`** in `_canon.yaml`.
   This flips MP1 from HIGH-severity enforcement to LOW-severity
   surfacing. CI no longer gates, but every imported provider SDK
   is still listed on every `myco immune` run, so the boundary's
   status is never hidden.

2. **Run `myco molt`** (or the v0.5 equivalent) to bump
   `contract_version` and write an entry in
   `docs/contract_changelog.md` naming the provider and the failure
   mode it introduces. Every consumer sees the bump on next pull.

3. **Land a craft document** under `docs/primordia/` that argues
   the case through the usual three rounds of self-debate / refute /
   reflect. Name the provider, list the ways it can fail, describe
   the fallback path when the provider is down, and articulate why
   routing the call through the agent surface is not acceptable.

All three together are the contract. Skipping any one of them makes
the substrate quietly inconsistent in a way that MP1 was designed
to prevent.

## Reversing the decision

Deleting every module under `providers/` and flipping
`no_llm_in_substrate` back to `true` re-engages MP1's HIGH-severity
enforcement. Bump the contract again (`myco molt`) so the reversal
is recorded. The escape hatch is symmetric on purpose: Myco's
position on LLM coupling is a policy knob, not a one-way door.

## For most substrates

**Leave this directory empty.** The kernel itself should never
need to call an LLM — that is what the agent is for. An ingestion
adapter, a digestion pipeline, a circulation pass: none of these
should know about any provider. If you find yourself reaching for
an OpenAI import inside `src/myco/`, the right next step is almost
always to move the decision out of the kernel and into an agent
tool invocation.
