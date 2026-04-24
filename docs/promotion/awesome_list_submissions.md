# Awesome-list submission patches

Pre-written entries for major "awesome-*" lists on GitHub. Each
entry is crafted to match that list's formatting conventions.
You fork, edit, open PR; the text here is the one-line + link
that goes in.

## Workflow for each submission

```bash
# Example: awesome-python
gh repo fork vinta/awesome-python --clone
cd awesome-python
# Find the right section (usually by grep for a similar project)
# Add the Myco entry per this doc's template
git checkout -b add-myco
git commit -am "Add Myco to AI / Agent Memory"
gh pr create --fill
```

Open PRs to **at most one list per day** so maintainers don't
pattern-match you as a spammer. Expect ~30% acceptance rate
across the 10 lists below; some are strict about
"production-ready" gates Myco doesn't meet yet.

---

## Primary targets (high value, MCP/AI-focused)

### 1. [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers)

**Section**: Third-party servers (community-maintained MCP servers)
**File**: `README.md` → "Third-party servers" section, alphabetical

```markdown
- **[Myco](https://github.com/Battam1111/Myco)**: A long-lived cognitive substrate for LLM agents. 19 verbs (ingest / digest / traverse / immune / molt / excrete / and more), 25 lint dimensions, self-validating graph, editable-default install. Exposes all verbs as MCP tools with an R1 through R7 pulse sidecar on every tool response. A-tier on Glama's Tool Definition Quality rubric.
```

**PR title**: `Add Myco: cognitive substrate for LLM agents`
**PR body**: link to repo, call out MCP tool surface (19 tools)
+ pulse sidecar + 10-host install CLI.

### 2. [punkpeye/awesome-mcp-servers](https://github.com/punkpeye/awesome-mcp-servers)

**Section**: Depends on the list's current structure. Likely
"Knowledge & Memory" or "Data & File Systems".
**File**: `README.md`

```markdown
- [Myco](https://github.com/Battam1111/Myco) - Agent-first cognitive substrate. 19 verbs exposed as MCP tools, 25 lint dims, editable kernel. Cross-session / cross-project memory via an on-disk markdown+YAML tree. Provider-agnostic (MP1/MP2 enforce no LLM-SDK imports in kernel + plugins). A-tier on Glama's TDQS rubric.
```

### 3. [wong2/awesome-mcp-servers](https://github.com/wong2/awesome-mcp-servers)

Similar to #2; check the list's current section structure
before submitting. Format usually matches.

### 4. [appcypher/awesome-mcp-servers](https://github.com/appcypher/awesome-mcp-servers)

Another community MCP list. Same entry shape as #2.

---

## Secondary targets (LLM / AI-tooling generic)

### 5. [Hannibal046/Awesome-LLM](https://github.com/Hannibal046/Awesome-LLM)

**Section**: "Useful Resources" → subsection "LLM Applications" or
"LLM Agents"

```markdown
- [Myco](https://github.com/Battam1111/Myco) - Self-validating cognitive substrate for LLM agents. 19-verb CLI+MCP surface, 25 lint dimensions, contract-governed evolution via a 3-round craft loop. Python 3.10+. MIT.
```

### 6. [e2b-dev/awesome-ai-agents](https://github.com/e2b-dev/awesome-ai-agents)

**Section**: "Agent Frameworks" or "Memory"; check current
structure.

```markdown
- **Myco**: Long-term memory substrate (19 verbs, 25 lint dims). Not a framework; designed to layer below LangChain / CrewAI / DSPy. [repo](https://github.com/Battam1111/Myco) · [PyPI](https://pypi.org/project/myco/)
```

### 7. [steven2358/awesome-generative-ai](https://github.com/steven2358/awesome-generative-ai)

Broader scope; may or may not accept tooling. Try the "Agents"
or "Frameworks" section; entry shape per list convention.

---

## Tertiary targets (Python / lint / infrastructure)

### 8. [vinta/awesome-python](https://github.com/vinta/awesome-python)

Gatekept; many projects rejected. Worth trying with a short,
specific entry in "Machine Learning" or "Command-line Tools".

```markdown
* [Myco](https://github.com/Battam1111/Myco) - Agent-first cognitive substrate (19 CLI verbs + MCP server) for long-running LLM agents. Self-validating graph, editable-default install.
```

### 9. [ml-tooling/best-of-ml-python](https://github.com/ml-tooling/best-of-ml-python)

Automated + curated; submissions go through a specific PR flow
described in their CONTRIBUTING. Follow their template; Myco
fits under "ML Applications" likely.

### 10. [sindresorhus/awesome](https://github.com/sindresorhus/awesome)

Not Myco's target directly (this is the meta-list of awesome
lists). Skip unless you create a sub-awesome-list yourself.

---

## Format reminders

Each awesome list has its own micro-conventions:

- Alphabetical ordering within a section (usually).
- Emoji / icon prefixes in some lists, plain text in others.
- Em-dash vs hyphen separator between name and description.
- "MIT" or "Python 3.10+" tag conventions.

Before opening a PR, search the list for a similar entry and
mirror its exact format. Maintainers reject PRs that break
convention far more often than ones that break accuracy.

---

## MCP-registry-specific submissions

Beyond the awesome lists, Myco as an MCP server may qualify
for the Anthropic connector registry once there's a public
submission path. Watch the [modelcontextprotocol blog](https://modelcontextprotocol.io/blog)
for that announcement; as of 2026-04, the registry intake flow
is manual.

Separate submission file:
[`mcp_registry_submission.md`](mcp_registry_submission.md).

---

## Rejection handling

If a maintainer rejects a PR ("doesn't fit scope", "not
production-ready yet", "too niche"), accept gracefully. Three
rules:

1. **Don't argue.** The maintainer's call on their own list is
   final. Arguing burns goodwill for the next submission.
2. **Thank them briefly**, close the PR.
3. **Wait 90 days + 1 MAJOR release before re-submitting.** A
   resubmission that can cite concrete adoption signals (stars,
   downloads, production users) is much more likely to land.

## Tracking submissions

Keep a local checklist (in your own notes/ ingestion via `myco
eat`, naturally) tracking which lists you've submitted to, on
what date, and the current PR state. The list's own issues /
discussions tab often has a "pending PRs" overview.
