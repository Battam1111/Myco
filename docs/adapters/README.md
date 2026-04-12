# Myco Adapters

Adapters define how external tools and knowledge systems integrate with Myco's four-layer architecture.

## Philosophy

Myco doesn't replace your existing tools — it metabolizes them. An adapter is the protocol that bridges an external tool's output into Myco's evolution cycle.

Adapters come in three types based on their integration model:
- **Content import** (Hermes, OpenClaw): migrate existing tool knowledge into Myco's layers
- **Coexistence guide** (Cursor, GPT): configure a different agent type to work alongside Myco
- **L0 backend** (MemPalace): plug in a retrieval service as Myco's archive layer

In the current pre-release (package v0.2.0, kernel contract v0.45.0), content-import adapters are available as CLI commands for Hermes and OpenClaw (`myco import --from hermes ./skills/`) and as manual protocols for the rest. Coexistence adapters are ready to use today — no CLI automation needed, just follow the YAML. L0 backends (MemPalace) remain design-spec until the first real deployment.

## Adapter Schema

**Coexistence adapters** (Cursor, GPT) use agent-specific fields:
```yaml
name, version, description, agent_type, integration_model,
setup_steps, cursorrules_snippet (if applicable),
coexistence_notes, layer_mapping, workflow_compatibility,
value_proposition, limitations, roadmap, notes
```

**Content import adapters** (Hermes, OpenClaw) use:
```yaml
name, version, description, source_type, integration_type, target_layer,
import_steps, layer_mapping, lint_checks, value_proposition, roadmap, notes
```

**L0 backend adapters** (MemPalace) use:
```yaml
name, version, description, source_type, integration_type, target_layer,
architecture, import_steps, canon_extension, layer_mapping,
lint_checks, promotion_loop, value_proposition, roadmap, notes
```

## Available Adapters

| Tool | Integration Type | Status | Notes |
|------|-----------------|--------|-------|
| [Claude Code (CLAUDE.md)](./claude_code.yaml) | Entry Point Upgrade | ✅ CLI | `myco migrate --entry-point CLAUDE.md` |
| [Cursor](./cursor.yaml) | Coexistence Guide | ✅ Active | File-aware coexistence, no migration needed |
| [GPT (OpenAI)](./gpt.yaml) | Coexistence Guide | ✅ Active | System prompt / ChatGPT Projects / Assistants API |
| [Hermes Agent](./hermes.yaml) | Content Import (Skills) | ✅ CLI | `myco import --from hermes ./skills/` |
| [OpenClaw (MEMORY.md)](./openclaw.yaml) | Content Import (Memory) | ✅ CLI | `myco import --from openclaw ./MEMORY.md` |
| [MemPalace](./mempalace.yaml) | L0 Retrieval Backend | 📋 Design spec | Post-1.0 API integration |

## Contributing an Adapter

If you've successfully integrated another tool with Myco, please submit an adapter:

1. Copy this schema, fill in for your tool
2. Test the import steps manually on your project
3. Confirm `myco lint` passes after the import
4. Submit a PR with your `docs/adapters/<toolname>.yaml`

Acceptance criteria: Manually tested on ≥1 real project. All lint checks pass.

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.

---

← [Back to Myco root](../README.md)
