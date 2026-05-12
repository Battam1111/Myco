# examples/

Runnable sample Myco substrates. Each example is a complete
substrate tree you can `cd` into and drive with `myco` verbs; it
demonstrates one load-bearing use case + the minimal doctrine
fences needed to support it.

> **Agent-first note**: every example is described in terms an
> LLM agent reading this tree can execute literally. The
> command blocks are copy-paste-ready. They assume nothing
> beyond `pip install myco` + a terminal.

## Index

### Sample substrates

| Dir | Use case | Verbs exercised | Size |
|---|---|---|---|
| [`minimal/`](minimal/README.md) | Smallest possible working substrate | `germinate` / `eat` / `hunger` / `assimilate` / `immune` | ~5 files |
| [`research-assistant/`](research-assistant/README.md) | Solo-researcher knowledge base (papers + decisions + frictions) | full 20-verb surface; propagate out to a derived substrate | ~15 files after use |

### Framework integration demos (v0.7.10+; install via `pip install 'myco[examples]'`)

Each demo runs Myco's 20 verbs as MCP tools driven by a different
agent framework. All 8 ship a `main.py` with a `main(dry: bool=False)
-> int` entry point + a minimal README. Smoke-tested in CI via
`.tests/integration/examples/test_examples_smoke.py`.

| Dir | Framework | Probe import |
|---|---|---|
| [`agno-myco-demo/`](agno-myco-demo/README.md) | Agno | `agno` |
| [`claude-sdk-myco-demo/`](claude-sdk-myco-demo/README.md) | Claude Agent SDK | `claude_agent_sdk` |
| [`crewai-myco-demo/`](crewai-myco-demo/README.md) | CrewAI | `crewai` |
| [`dspy-myco-demo/`](dspy-myco-demo/README.md) | DSPy | `dspy` |
| [`langgraph-myco-demo/`](langgraph-myco-demo/README.md) | LangGraph | `langchain_mcp_adapters` |
| [`microsoft-agent-framework-myco-demo/`](microsoft-agent-framework-myco-demo/README.md) | Microsoft Agent Framework | `agent_framework` |
| [`praisonai-myco-demo/`](praisonai-myco-demo/README.md) | PraisonAI | `praisonaiagents` |
| [`smolagents-myco-demo/`](smolagents-myco-demo/README.md) | smolagents | `smolagents` |

## Running an example

```bash
cd examples/minimal
python -m myco hunger      # R1: what does the substrate need?
python -m myco immune      # current lint baseline
python -m myco eat --content "hello from example"
python -m myco assimilate  # promote raw to integrated
python -m myco senesce     # R2: clean end-of-session
```

Every example substrate is self-contained; nothing outside its
directory is read or written. Delete the directory when you're
done and nothing leaks.

## What these examples are NOT

- **Not tutorials.** Myco's tutorial lives in the top-level
  README's "Quick Start" section. These examples are reference
  substrates for agents + humans who have already read the
  tutorial.
- **Not starter templates.** Use `myco germinate` to start a
  fresh substrate; that gives you the canonical minimal shape.
  Examples here may carry use-case-specific customisation an
  ordinary substrate shouldn't inherit.
- **Not benchmarks.** `tests/` is where correctness lives.
  Examples demonstrate *intent*, not *coverage*.
