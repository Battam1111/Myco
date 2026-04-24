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

| Dir | Use case | Verbs exercised | Size |
|---|---|---|---|
| [`minimal/`](minimal/) | Smallest possible working substrate | `germinate` / `eat` / `hunger` / `assimilate` / `immune` | ~5 files |
| [`research-assistant/`](research-assistant/) | Solo-researcher knowledge base (papers + decisions + frictions) | full 19-verb surface; propagate out to a derived substrate | ~15 files after use |

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
