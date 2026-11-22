# MCPIdhall

Serveur MCP (**FastMCP**) lecture/écriture pour l'API REST **IDhall v1** (*Humanperf Software*), conçu pour que **chaque utilisateur fournisse son propre jeton JWT IDhall** (et hérite ainsi strictement de ses permissions RBAC dans IDhall).

---

## Prérequis & Installation

```bash
uv sync --extra dev
```

---

## Authentification par utilisateur (JWT)

Chaque utilisateur génère son propre jeton JWT dans IDhall :
`Mon compte > Connexion et sécurité > Jetons d'authentification pour l'API REST`

Le serveur résout le jeton **par requête** (aucun jeton partagé en mémoire) :

1. **Mode multi-utilisateurs HTTP (`streamable-http` ou `sse`)** — *recommandé pour une équipe* :
   - Chaque client MCP transmet le jeton de l'utilisateur dans l'en-tête HTTP :
     `Authorization: Bearer <votre_jwt_idhall>`
   - L'URL de l'instance IDhall est automatiquement déduite du claim `iss` du JWT (ex. `https://mon-entreprise.idhall.com`), ou peut être forcée via `IDHALL_BASE_URL` / l'en-tête `X-IDhall-Base-Url` (protégé contre le SSRF : HTTPS uniquement + hôte `*.idhall.com` ou liste `IDHALL_ALLOWED_HOSTS`).
   - Par sécurité, le fichier `.env` n'est **pas** chargé automatiquement en mode HTTP afin d'éviter toute fuite d'un jeton serveur vers des clients non authentifiés.

   ```bash
   uv run mcp-idhall --transport streamable-http --host 0.0.0.0 --port 8000
   ```

2. **Mode local `stdio`** — *poste individuel (Antigravity, Claude Desktop, Cursor…)* :
   - Chaque utilisateur configure son propre `IDHALL_API_TOKEN` dans la configuration de son client MCP (ou dans `.env` local) :

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

---

## Outils MCP exposés (32 outils — 100 % des 208 endpoints couverts)

* **Identité & Introspection (4)** : `idhall_about`, `idhall_whoami`, `idhall_search_endpoints`, `idhall_get_endpoint_spec`
* **Initiatives CRUD & brouillons (9)** : `idhall_list_ideas`, `idhall_count_ideas`, `idhall_get_idea`, `idhall_get_idea_input_availability`, `idhall_create_idea`, `idhall_create_idea_draft`, `idhall_publish_idea_draft`, `idhall_update_idea`, `idhall_delete_idea`
* **Workflow / Traitement (2)** : `idhall_get_idea_stage`, `idhall_transition_idea_stage` *(10 transitions + annulation)*
* **Mise en œuvre & Plan d'action (7)** : `idhall_get_idea_implementation`, `idhall_update_idea_implementation_progress`, `idhall_list_action_plan_tasks`, `idhall_create_action_plan_task`, `idhall_update_action_plan_task`, `idhall_update_task_progress`, `idhall_delete_action_plan_task`
* **Collaboration & Opportunité (7)** : `idhall_list_idea_contributions`, `idhall_add_idea_contribution`, `idhall_get_idea_memo`, `idhall_set_idea_memo`, `idhall_get_idea_tags`, `idhall_manage_idea_tags`, `idhall_get_opportunity_analysis`
* **Utilisateurs & Référentiels (3)** : `idhall_list_users`, `idhall_get_user`, `idhall_list_reference_items`
* **Outil universel (1)** : `idhall_api_request` *(permet d'appeler n'importe lequel des 208 endpoints documentés en `GET`/`POST`/`PUT`/`PATCH`/`DELETE`)*

---

## Documentation générée & Tests

* [**`docs/GUIDE_UTILISATEUR.md`**](docs/GUIDE_UTILISATEUR.md) — **Guide utilisateur détaillé pas à pas (du débutant au professionnel)**
* [**`docs/GUIDE_DOCKER_PORTAINER.md`**](docs/GUIDE_DOCKER_PORTAINER.md) — **Guide de déploiement Docker simple, Portainer & Nginx Proxy Manager (débutants)**
* [`docs/IDHALL_API_SYNTHESE.md`](docs/IDHALL_API_SYNTHESE.md) — Synthèse complète des 208 endpoints
* [`docs/openapi.json`](docs/openapi.json) — Spécification OpenAPI 3.1.0 (128 chemins, 125 schémas)
* [`docs/idhall_api_reference.json`](docs/idhall_api_reference.json) — Export brut complet du référentiel IDhall

```bash
uv run pytest -v
```

---

## Licence

Distribué sous licence **Apache 2.0** — voir [`LICENSE`](LICENSE).
