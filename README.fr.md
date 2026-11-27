# MCPIdhall — Serveur MCP (FastMCP) pour l'API REST IDhall

> [🇬🇧 **English version (README.md)**](README.md) | 🇫🇷 **Français**

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![FastMCP](https://img.shields.io/badge/MCP-FastMCP_4-6E56CF)](src/mcp_idhall/server.py)
[![OpenAPI](https://img.shields.io/badge/OpenAPI-3.1.0_(208_endpoints)-6BA539?logo=openapiinitiative&logoColor=white)](docs/openapi.json)
[![Docker](https://img.shields.io/badge/Docker-amd64_%7C_arm64-2496ED?logo=docker&logoColor=white)](Dockerfile)
[![Build & Publish Docker](https://github.com/smilebob/MCPIdhall/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/smilebob/MCPIdhall/actions/workflows/docker-publish.yml)

**MCPIdhall** est un serveur **Model Context Protocol (MCP)** open-source basé sur **FastMCP**, offrant un accès **lecture et écriture** complet à l'**API REST v1 d'IDhall** (*Humanperf Software* — plateforme de management de l'innovation, d'amélioration continue et de plans d'action).

---

## Points forts

* **Authentification JWT par utilisateur (RBAC strict) :** chaque utilisateur fournit son propre jeton JWT IDhall ; aucun secret partagé côté serveur.
* **100 % des 208 endpoints IDhall v1 couverts :** 33 outils métier typés (initiatives, brouillons, workflow, plans d'action, contributions, mémo, tags, analyse d'opportunité, utilisateurs, 23 référentiels) + un outil universel `idhall_api_request` couplé à un catalogue local instantané (0 requête réseau).
* **Double transport :** `stdio` (local : Antigravity, Claude Desktop, Cursor, VS Code) et `streamable-http` / `sse` (serveur d'équipe multi-utilisateurs).
* **Résilient & sécurisé :** backoff exponentiel automatique sur `HTTP 429` / `5xx`, erreurs RFC 7807 formatées, image Docker non-root `read_only` multi-arch (`amd64`/`arm64`) publiée sur **GHCR**.
* **Documentation complète bilingue (FR / EN) :** spécification **OpenAPI 3.1.0** (`128` chemins, `125` schémas), synthèse des 208 endpoints, guide utilisateur pas à pas et guide Docker / Portainer / Nginx Proxy Manager.

---

## Démarrage rapide

### 1. En local (`stdio` — Antigravity, Claude Desktop, Cursor, VS Code)

```bash
git clone https://github.com/smilebob/MCPIdhall.git
cd MCPIdhall
uv sync
```

Ajoutez dans la configuration MCP de votre client IA avec votre propre jeton JWT IDhall (`Mon compte > Connexion et sécurité > Jetons d'authentification pour l'API REST`) :

```json
{
  "mcpServers": {
    "idhall": {
      "command": "uv",
      "args": ["--directory", "/chemin/vers/MCPIdhall", "run", "mcp-idhall"],
      "env": {
        "IDHALL_API_TOKEN": "<votre_jeton_jwt_idhall>"
      }
    }
  }
}
```

### 2. En serveur d'équipe multi-utilisateurs (`Docker` / `Portainer` / `streamable-http`)

```bash
docker run -d \
  --name mcp-idhall \
  --restart unless-stopped \
  -p 127.0.0.1:8000:8000 \
  -e IDHALL_ALLOWED_HOSTS="*" \
  -e IDHALL_LANGUAGE="fr" \
  -e IDHALL_TIMEZONE="Europe/Paris" \
  ghcr.io/smilebob/mcpidhall:latest
```

Chaque client MCP distant se connecte en HTTPS avec son propre jeton :

```json
{
  "mcpServers": {
    "idhall": {
      "url": "https://mcp-idhall.votre-domaine.fr/mcp",
      "headers": {
        "Authorization": "Bearer <votre_jeton_jwt_idhall>"
      }
    }
  }
}
```

*(L'URL de l'instance IDhall est déduite automatiquement du claim `iss` du JWT, ou surchargeable via `IDHALL_BASE_URL` / `X-IDhall-Base-Url`.)*

---

## Outils MCP exposés (33 outils — 100 % des 208 endpoints)

| Catégorie | Outils |
| :--- | :--- |
| **Identité & Introspection (4)** | `idhall_about`, `idhall_whoami`, `idhall_search_endpoints`, `idhall_get_endpoint_spec` |
| **Initiatives CRUD & brouillons (9)** | `idhall_list_ideas`, `idhall_count_ideas`, `idhall_get_idea`, `idhall_get_idea_input_availability`, `idhall_create_idea`, `idhall_create_idea_draft`, `idhall_publish_idea_draft`, `idhall_update_idea`, `idhall_delete_idea` |
| **Workflow / Traitement (2)** | `idhall_get_idea_stage`, `idhall_transition_idea_stage` *(10 transitions + annulation)* |
| **Mise en œuvre & Plan d'action (7)** | `idhall_get_idea_implementation`, `idhall_update_idea_implementation_progress`, `idhall_list_action_plan_tasks`, `idhall_create_action_plan_task`, `idhall_update_action_plan_task`, `idhall_update_task_progress`, `idhall_delete_action_plan_task` |
| **Collaboration & Opportunité (7)** | `idhall_list_idea_contributions`, `idhall_add_idea_contribution`, `idhall_get_idea_memo`, `idhall_set_idea_memo`, `idhall_get_idea_tags`, `idhall_manage_idea_tags`, `idhall_get_opportunity_analysis` |
| **Utilisateurs & Référentiels (3)** | `idhall_list_users`, `idhall_get_user`, `idhall_list_reference_items` *(23 référentiels : axes, sites, services, catégories, risques, parties prenantes…)* |
| **Universel (1)** | `idhall_api_request` *(accès complet aux 208 endpoints en `GET`/`POST`/`PUT`/`PATCH`/`DELETE`)* |

---

## Documentation & Ressources

| Document | 🇫🇷 Français | 🇬🇧 English |
| :--- | :--- | :--- |
| **Présentation du projet** | [`README.fr.md`](README.fr.md) | [`README.md`](README.md) |
| **Guide utilisateur (Débutant à Pro)** | [`docs/GUIDE_UTILISATEUR.md`](docs/GUIDE_UTILISATEUR.md) | [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) |
| **Guide Docker, Portainer & NPM** | [`docs/GUIDE_DOCKER_PORTAINER.md`](docs/GUIDE_DOCKER_PORTAINER.md) | [`docs/DOCKER_PORTAINER_GUIDE.md`](docs/DOCKER_PORTAINER_GUIDE.md) |
| **Skill Agent (Antigravity)** | [`skills/idhall/SKILL.md`](skills/idhall/SKILL.md) | [`skills/idhall/SKILL.md`](skills/idhall/SKILL.md) |
| **Spécification OpenAPI 3.1.0** | [`docs/openapi.json`](docs/openapi.json) | [`docs/openapi.json`](docs/openapi.json) |
| **Synthèse API (208 endpoints)** | [`docs/IDHALL_API_SYNTHESE.md`](docs/IDHALL_API_SYNTHESE.md) | [`docs/IDHALL_API_SYNTHESE.md`](docs/IDHALL_API_SYNTHESE.md) |

### Installer la Skill Agent (Antigravity)

```bash
mkdir -p ~/.gemini/config/skills
cp -r skills/idhall ~/.gemini/config/skills/
```

## Tests

```bash
uv sync --extra dev
uv run pytest -v
```

---

## Licence

Distribué sous licence **Apache 2.0** — voir [`LICENSE`](LICENSE).
*Ce projet communautaire n'est pas affilié à Humanperf Software.*
