# Claude Agent SDK + Myco demo

`pip install claude-agent-sdk myco[mcp]`

`python main.py` — agent boots with Myco's 20 verbs as MCP tools.
Query example: "Call myco_hunger then myco_brief."

The `setting_sources=["project"]` option auto-loads `.mcp.json`.
