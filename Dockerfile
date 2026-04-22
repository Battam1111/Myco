# syntax=docker/dockerfile:1.7
#
# Minimal OCI image for Myco's MCP server over stdio.
#
# Myco's primary install path is editable (`pip install -e`) —
# see CONTRIBUTING.md "Dev environment". This image is the
# "install from PyPI + start over stdio" path, used by:
#
#   - Glama's introspection check
#     (https://glama.ai/mcp/servers/Battam1111/Myco)
#   - Any MCP client that prefers OCI images over pip/pipx
#
# The `io.modelcontextprotocol.server.name` label is the
# MCP-Registry-defined ownership marker; clients that resolve
# OCI-registryType packages use it to verify the image belongs
# to the server's claimed namespace.

FROM python:3.12-slim

LABEL io.modelcontextprotocol.server.name="io.github.Battam1111/myco"
LABEL org.opencontainers.image.title="Myco"
LABEL org.opencontainers.image.description="Agent-first cognitive substrate for LLM agents. 18 verbs + 25 lint dims over a self-validating graph."
LABEL org.opencontainers.image.source="https://github.com/Battam1111/Myco"
LABEL org.opencontainers.image.documentation="https://github.com/Battam1111/Myco/tree/main/docs"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.authors="Battam1111"

# Install the latest released wheel from PyPI. Using a loose pin so
# image rebuilds pick up new patch releases automatically; pin
# tighter (`myco[mcp]==0.5.12`) if you want reproducible scans.
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir 'myco[mcp]'

# stdio transport — the MCP host pipes stdin/stdout into this
# process. Exec form so signals reach Python directly.
ENTRYPOINT ["mcp-server-myco"]
