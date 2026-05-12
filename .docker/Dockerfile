# syntax=docker/dockerfile:1.7
#
# Minimal OCI image for Myco's MCP server over stdio OR streamable-http.
#
# Myco's primary install path is editable (`pip install -e`);
# see .github/CONTRIBUTING.md "Dev environment". This image is the
# "install from PyPI + start over stdio/streamable-http" path, used by:
#
#   - Glama's introspection check
#     (https://glama.ai/mcp/servers/Battam1111/Myco)
#   - Any MCP client that prefers OCI images over pip/pipx
#   - Enterprise / multi-tenant deployments using streamable-http
#     (v0.6.0 default for OCI is streamable-http on port from
#     $MYCO_PORT env or kernel-allocated)
#
# The `io.modelcontextprotocol.server.name` label is the
# MCP-Registry-defined ownership marker; clients that resolve
# OCI-registryType packages use it to verify the image belongs
# to the server's claimed namespace.

FROM python:3.12-slim

LABEL io.modelcontextprotocol.server.name="io.github.Battam1111/myco"
LABEL org.opencontainers.image.title="Myco"
LABEL org.opencontainers.image.description="Agent-first cognitive substrate for LLM agents. 20 verbs + 50 lint dims + 7 subsystems over a self-validating graph (v0.8.5)."
LABEL org.opencontainers.image.source="https://github.com/Battam1111/Myco"
LABEL org.opencontainers.image.documentation="https://github.com/Battam1111/Myco/tree/main/.docs"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.authors="Battam1111"
LABEL org.opencontainers.image.version="0.8.5"

# v0.8.5: install with mcp + adapters + auth extras for full
# streamable-http + OAuth deployment.
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir 'myco[mcp,adapters,mcp-auth]'

# v0.6.0 §A6 streamable-http transport. Multi-container deployments
# should set MYCO_PORT in compose / k8s manifest to avoid collision.
# Default port=0 lets the kernel allocate.
ENV MYCO_PORT=0
ENV MYCO_HOST=0.0.0.0
ENV MYCO_MOUNT_PATH=/mcp

# Both transports supported. stdio is default for legacy compatibility;
# streamable-http exposes 8000 by convention.
EXPOSE 8000

# Default command: stdio (legacy clients pipe stdin/stdout).
# To run streamable-http instead, override CMD:
#   docker run -p 8000:8000 myco python -m myco.mcp --transport streamable-http --host 0.0.0.0 --port 8000
CMD ["mcp-server-myco"]
