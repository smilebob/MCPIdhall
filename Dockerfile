# syntax=docker/dockerfile:1.7

# =============================================================================
# Stage 1 : Build de l'environnement virtuel avec uv
# =============================================================================
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Installe les dépendances d'abord (meilleur cache Docker)
COPY pyproject.toml uv.lock README.md ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Copie le code source et le catalogue local des 208 endpoints, puis installe le package
COPY src ./src
COPY docs/idhall_api_reference.json ./docs/idhall_api_reference.json
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev


# =============================================================================
# Stage 2 : Image runtime minimale et durcie (utilisateur non-root)
# =============================================================================
FROM python:3.13-slim-bookworm AS runtime

LABEL org.opencontainers.image.title="MCPIdhall" \
      org.opencontainers.image.description="Serveur MCP (FastMCP) lecture/écriture pour l'API REST IDhall avec JWT par utilisateur" \
      org.opencontainers.image.source="https://github.com/smilebob/MCPIdhall" \
      org.opencontainers.image.licenses="Apache-2.0"

# Utilisateur non-root dédié
RUN groupadd --system --gid 10001 mcpuser \
    && useradd --system --uid 10001 --gid mcpuser --home-dir /app --shell /usr/sbin/nologin mcpuser

WORKDIR /app

COPY --from=builder --chown=mcpuser:mcpuser /app/.venv /app/.venv
COPY --from=builder --chown=mcpuser:mcpuser /app/src /app/src
COPY --from=builder --chown=mcpuser:mcpuser /app/docs/idhall_api_reference.json /app/docs/idhall_api_reference.json

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    MCP_TRANSPORT="streamable-http" \
    MCP_HOST="0.0.0.0" \
    MCP_PORT="8000" \
    IDHALL_ALLOWED_HOSTS="*" \
    IDHALL_LANGUAGE="fr" \
    IDHALL_REFERENCE_JSON="/app/docs/idhall_api_reference.json"

USER mcpuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"MCP_PORT\", \"8000\")}/health', timeout=3)" || exit 1

ENTRYPOINT ["mcp-idhall"]
