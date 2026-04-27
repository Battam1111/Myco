# LangGraph + Myco MCP demo

`pip install langgraph langchain-mcp-adapters myco[mcp]`

LangGraph node consumes Myco MCP tools as native LangChain Tool
objects via `langchain-mcp-adapters`. The Memory node uses
`myco_sense` instead of vector retrieval — anti-RAG memory pattern.

`python main.py` lists discovered Myco tools.
