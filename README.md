# MCPIdhall — FastMCP Server for the IDhall REST API

> 🇬🇧 **English** | [🇫🇷 **Version française (README.fr.md)**](README.fr.md)

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![FastMCP](https://img.shields.io/badge/MCP-FastMCP_4-6E56CF)](src/mcp_idhall/server.py)
[![OpenAPI](https://img.shields.io/badge/OpenAPI-3.1.0_(208_endpoints)-6BA539?logo=openapiinitiative&logoColor=white)](docs/openapi.json)
[![Docker](https://img.shields.io/badge/Docker-amd64_%7C_arm64-2496ED?logo=docker&logoColor=white)](Dockerfile)
[![Build & Publish Docker](https://github.com/smilebob/MCPIdhall/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/smilebob/MCPIdhall/actions/workflows/docker-publish.yml)

**MCPIdhall** is an open-source **Model Context Protocol (MCP)** server built with **FastMCP**, providing full **read/write** access to the **IDhall REST API v1** (*Humanperf Software* — innovation management, continuous improvement, and action plan platform).

---

## Key Features

* **Per-User JWT Authentication (Strict RBAC):** Every user supplies their own IDhall JWT token; no shared credentials are stored on the server. All actions strictly respect each user's IDhall access profile.
* **100% Coverage of All 208 IDhall v1 Endpoints:** 33 curated, strongly-typed tools (initiatives, drafts, workflow transitions, action plans, contributions, memos, tags, opportunity analysis, users, 23 reference catalogs) + a universal `idhall_api_request` escape-hatch tool backed by a zero-latency local endpoint catalog.
* **Dual Transport:** `stdio` (local desktop clients: Antigravity, Claude Desktop, Cursor, VS Code) and `streamable-http` / `sse` (shared multi-user team server).
* **Resilient & Hardened:** Automatic exponential backoff on `HTTP 429` / `5xx`, structured RFC 7807 `application/problem+json` error formatting, non-root `read_only` multi-arch (`amd64`/`arm64`) Docker image published to **GHCR**.
* **Complete Bilingual Documentation (EN / FR):** Embedded **OpenAPI 3.1.0** specification (`128` paths, `125` schemas), complete 208-endpoint synthesis, step-by-step user guide, and beginner-friendly Docker / Portainer / Nginx Proxy Manager guide.

---

## Quick Start

### 1. Local Mode (`stdio` — Antigravity, Claude Desktop, Cursor, VS Code)

```bash
git clone https://github.com/smilebob/MCPIdhall.git
cd MCPIdhall
uv sync
```

Add the server to your MCP client configuration with your personal IDhall JWT token (`My Account > Login & Security > REST API authentication tokens`):

```json
{
  "mcpServers": {
    "idhall": {
      "command": "uv",
      "args": ["--directory", "/path/to/MCPIdhall", "run", "mcp-idhall"],
      "env": {
        "IDHALL_API_TOKEN": "<your_idhall_jwt_token>"
      }
    }
  }
}
```

### 2. Multi-User Team Server (`Docker` / `Portainer` / `streamable-http`)

```bash
docker run -d \
  --name mcp-idhall \
  --restart unless-stopped \
  -p 127.0.0.1:8000:8000 \
  -e IDHALL_ALLOWED_HOSTS="*" \
  -e IDHALL_LANGUAGE="en" \
  -e IDHALL_TIMEZONE="UTC" \
  ghcr.io/smilebob/mcpidhall:latest
```

Each remote MCP client connects over HTTPS with its own user JWT:

```json
{
  "mcpServers": {
    "idhall": {
      "url": "https://mcp-idhall.your-domain.com/mcp",
      "headers": {
        "Authorization": "Bearer <your_idhall_jwt_token>"
      }
    }
  }
}
```

*(Your IDhall instance URL is automatically inferred from the JWT `iss` claim, or can be overridden via `IDHALL_BASE_URL` / `X-IDhall-Base-Url`.)*

---

## Exposed MCP Tools (33 Tools — 100% of 208 Endpoints)

| Category | Tools |
| :--- | :--- |
| **Identity & Discovery (4)** | `idhall_about`, `idhall_whoami`, `idhall_search_endpoints`, `idhall_get_endpoint_spec` |
| **Initiatives CRUD & Drafts (9)** | `idhall_list_ideas`, `idhall_count_ideas`, `idhall_get_idea`, `idhall_get_idea_input_availability`, `idhall_create_idea`, `idhall_create_idea_draft`, `idhall_publish_idea_draft`, `idhall_update_idea`, `idhall_delete_idea` |
| **Workflow & Stages (2)** | `idhall_get_idea_stage`, `idhall_transition_idea_stage` *(10 transitions + cancel)* |
| **Implementation & Action Plans (7)** | `idhall_get_idea_implementation`, `idhall_update_idea_implementation_progress`, `idhall_list_action_plan_tasks`, `idhall_create_action_plan_task`, `idhall_update_action_plan_task`, `idhall_update_task_progress`, `idhall_delete_action_plan_task` |
| **Collaboration & Opportunity (7)** | `idhall_list_idea_contributions`, `idhall_add_idea_contribution`, `idhall_get_idea_memo`, `idhall_set_idea_memo`, `idhall_get_idea_tags`, `idhall_manage_idea_tags`, `idhall_get_opportunity_analysis` |
| **Users & Reference Data (3)** | `idhall_list_users`, `idhall_get_user`, `idhall_list_reference_items` *(23 catalogs: plans, sites, organizations, categories, risks, stakeholders…)* |
| **Universal Escape Hatch (1)** | `idhall_api_request` *(full `GET`/`POST`/`PUT`/`PATCH`/`DELETE` access to all 208 endpoints)* |

---

## Documentation & Resources

| Document | 🇬🇧 English | 🇫🇷 Français |
| :--- | :--- | :--- |
| **Project Overview** | [`README.md`](README.md) | [`README.fr.md`](README.fr.md) |
| **User Guide (Beginner to Pro)** | [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) | [`docs/GUIDE_UTILISATEUR.md`](docs/GUIDE_UTILISATEUR.md) |
| **Docker, Portainer & NPM Guide** | [`docs/DOCKER_PORTAINER_GUIDE.md`](docs/DOCKER_PORTAINER_GUIDE.md) | [`docs/GUIDE_DOCKER_PORTAINER.md`](docs/GUIDE_DOCKER_PORTAINER.md) |
| **OpenAPI 3.1.0 Spec (208 endpoints)** | [`docs/openapi.json`](docs/openapi.json) | [`docs/openapi.json`](docs/openapi.json) |
| **API Synthesis (208 endpoints)** | [`docs/IDHALL_API_SYNTHESE.md`](docs/IDHALL_API_SYNTHESE.md) | [`docs/IDHALL_API_SYNTHESE.md`](docs/IDHALL_API_SYNTHESE.md) |

## Running Tests

```bash
uv sync --extra dev
uv run pytest -v
```

---

## License

Licensed under the **Apache License 2.0** — see [`LICENSE`](LICENSE).
*This is a community open-source project and is not affiliated with Humanperf Software.*
