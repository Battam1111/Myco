# MCP registry submission templates

Brief registry-entry-shaped content for MCP server directories.
Most MCP registries take a structured form (JSON, YAML, or a
single README bullet). These are pre-filled so submission is
copy-paste.

## Fields commonly requested

| Field | Myco value |
|---|---|
| Name | Myco |
| Server type | stdio (with optional sse + streamable-http) |
| Short description (≤ 120 chars) | "Cognitive substrate for LLM agents. 18 verbs expose ingest/digest/traverse/immune/molt — cross-session, cross-project memory." |
| Long description (300-500 chars) | "Myco is a long-lived, self-validating filesystem shape + manifest-driven verb surface for LLM agents. Every one of its 18 verbs (germinate / hunger / eat / sense / forage / assimilate / digest / sporulate / traverse / propagate / immune / senesce / fruit / molt / winnow / ramify / graft / brief) is exposed as an MCP tool. Tool responses carry a pulse sidecar echoing the L1 R1-R7 rules on every call. 25 lint dimensions enforce contract invariants mechanically. Provider-agnostic (MP1/MP2 mechanically forbid LLM-provider SDK imports in the kernel + plugins). Editable-default install. MIT." |
| Install command | `pip install 'myco[mcp]'` |
| Run command | `python -m myco.mcp --transport stdio` (or `sse` / `streamable-http`) |
| License | MIT |
| Language | Python |
| Min Python | 3.10 |
| Categories | Memory · Knowledge Management · Agents · Cognitive Architecture · MCP Servers |
| Keywords | agent-memory, long-term-memory, cognitive-substrate, self-evolving, mycelium, substrate, llm-memory, claude-code, cursor |
| Repo URL | https://github.com/Battam1111/Myco |
| PyPI URL | https://pypi.org/project/myco/ |
| Homepage | https://github.com/Battam1111/Myco |
| Issue tracker | https://github.com/Battam1111/Myco/issues |
| Maintainer | Battam1111 |
| Tool count | 18 |
| Prompts | 0 (uses pulse sidecar on every tool response instead of static prompts) |
| Resources | 0 (all state is filesystem; each substrate is its own resource dir) |

## JSON shape (for registries using JSON)

```json
{
  "name": "myco",
  "displayName": "Myco",
  "description": "Cognitive substrate for LLM agents. 18 verbs expose ingest/digest/traverse/immune/molt — cross-session, cross-project memory.",
  "homepage": "https://github.com/Battam1111/Myco",
  "repository": "https://github.com/Battam1111/Myco",
  "license": "MIT",
  "language": "python",
  "minPython": "3.10",
  "install": {
    "pip": "pip install 'myco[mcp]'"
  },
  "run": {
    "command": "python",
    "args": ["-m", "myco.mcp", "--transport", "stdio"]
  },
  "transports": ["stdio", "sse", "streamable-http"],
  "tools": 18,
  "categories": ["memory", "knowledge-management", "agents"],
  "keywords": [
    "agent-memory",
    "long-term-memory",
    "cognitive-substrate",
    "self-evolving",
    "mycelium",
    "substrate",
    "llm-memory"
  ],
  "author": "Battam1111"
}
```

## YAML shape (for registries using YAML)

```yaml
name: myco
displayName: Myco
description: "Cognitive substrate for LLM agents. 18 verbs expose ingest/digest/traverse/immune/molt — cross-session, cross-project memory."
homepage: https://github.com/Battam1111/Myco
repository: https://github.com/Battam1111/Myco
license: MIT
language: python
minPython: "3.10"
install:
  pip: "pip install 'myco[mcp]'"
run:
  command: python
  args: ["-m", "myco.mcp", "--transport", "stdio"]
transports: [stdio, sse, streamable-http]
tools: 18
categories:
  - memory
  - knowledge-management
  - agents
keywords:
  - agent-memory
  - long-term-memory
  - cognitive-substrate
  - self-evolving
  - mycelium
  - substrate
  - llm-memory
author: Battam1111
```

## Where to submit

1. **[modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)**
   — official list, "Third-party servers" README section.
   PR-based.
2. **[punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers)**
   — community list. PR-based.
3. **Anthropic connector registry** (once the public submission
   path is announced on https://modelcontextprotocol.io/blog) —
   likely form-based. Pre-filled fields above fit the expected shape.
4. **MCP server directory sites** (various hobbyist indexers) —
   usually form-based. The JSON / YAML shape above covers any.

Submit to #1 and #2 first; they're the canonical references
that downstream aggregators pick up automatically.
