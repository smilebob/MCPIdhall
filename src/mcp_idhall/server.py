"""Serveur MCP (FastMCP) lecture/écriture pour l'API REST IDhall v1.

Chaque utilisateur fournit son propre jeton JWT IDhall :
- En mode HTTP (streamable-http / sse) : via l'en-tête HTTP `Authorization: Bearer <jwt>`
  (et optionnellement `X-IDhall-Base-Url` si différent du claim `iss`).
- En mode stdio local : via la variable d'environnement `IDHALL_API_TOKEN`
  (et optionnellement `IDHALL_BASE_URL`).
"""

from __future__ import annotations

import argparse
import os
from typing import Any, Literal

from dotenv import load_dotenv
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from mcp_idhall import __version__
from mcp_idhall.auth import IDhallAuthError, resolve_credentials
from mcp_idhall.catalog import get_endpoint_spec, search_endpoints
from mcp_idhall.client import IDhallClient

mcp = FastMCP(
    name="MCPIdhall",
    instructions=(
        "Serveur MCP pour l'API REST IDhall (Humanperf Software, v1). "
        "Chaque appel s'exécute avec le jeton JWT personnel de l'utilisateur et respecte ses droits IDhall. "
        "Note importante : les appels GET retournent uniquement des champs minimaux (id, title) par défaut ; "
        "utilisez le paramètre `props` pour demander des propriétés supplémentaires, et utilisez "
        "`idhall_search_endpoints` + `idhall_get_endpoint_spec` pour découvrir les propriétés exactes "
        "ou les endpoints spécialisés avant d'appeler `idhall_api_request`."
    ),
)

REFERENCE_RESOURCES = Literal[
    "plans",
    "perspectives",
    "categories",
    "classes",
    "sites",
    "organizations",
    "processes",
    "products",
    "risks",
    "risk-types",
    "stakeholders",
    "stakeholder-types",
    "events",
    "event-types",
    "eval-scales",
    "eval-units",
    "user-profiles",
    "action-plan-templates",
    "phases-templates",
    "idea-selections",
    "idea-rejection-reasons",
    "idea-submission-guidances",
    "countries",
]

STAGE_TRANSITIONS = Literal[
    "standby",
    "change-approver",
    "request-details",
    "request-expertise",
    "approve--request-implementation-schedule",
    "approve--launch-implementation",
    "approve--end-implementation",
    "reject",
    "end-implementation",
    "close",
    "cancel",
]


def _get_client() -> IDhallClient:
    creds = resolve_credentials()
    return IDhallClient(creds)


# ---------------------------------------------------------------------------
# 1. Identité, Méta & Introspection du référentiel
# ---------------------------------------------------------------------------


@mcp.tool()
async def idhall_about() -> dict[str, Any]:
    """Retourne les informations sur la version d'IDhall et de son API REST."""
    return await _get_client().request("GET", "/api/v1/about")


@mcp.tool()
async def idhall_whoami(props: list[str] | None = None) -> dict[str, Any]:
    """Identifie l'utilisateur associé au jeton JWT courant et récupère sa fiche IDhall."""
    creds = resolve_credentials()
    claims = creds.claims or {}
    sub = claims.get("sub")
    user_data: Any = None
    if sub is not None:
        client = IDhallClient(creds)
        user_data = await client.request(
            "GET", f"/api/v1/users/{sub}", query_params={"props": props} if props else None
        )
    return {
        "base_url": creds.base_url,
        "jwt_claims": {
            "sub": sub,
            "name": claims.get("name"),
            "iss": claims.get("iss"),
            "exp": claims.get("exp"),
            "idhall:appver": claims.get("idhall:appver"),
        },
        "user": user_data,
    }


@mcp.tool()
def idhall_search_endpoints(
    query: str = "",
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] | None = None,
    limit: int = 25,
) -> list[dict[str, str]]:
    """Recherche dans le catalogue local des 208 endpoints IDhall v1 (zéro appel réseau).

    Utilisez cet outil pour trouver l'endpoint exact et son `endpoint_id` avant d'inspecter
    son schéma avec `idhall_get_endpoint_spec` ou d'appeler `idhall_api_request`.
    """
    return search_endpoints(query=query, method=method, limit=limit)


@mcp.tool()
async def idhall_get_endpoint_spec(endpoint_id: str) -> dict[str, Any]:
    """Retourne le schéma complet (paramètres, payload, classes, réponse) d'un endpoint IDhall.

    Lit d'abord le catalogue local ; interroge `/api/v1/reference/endpoints/{endpoint_id}` si absent.
    Exemple d'`endpoint_id` : `GET__ideas`, `POST__ideas`, `PATCH__ideas__(id)`.
    """
    local = get_endpoint_spec(endpoint_id)
    if local is not None:
        return local
    return await _get_client().request("GET", f"/api/v1/reference/endpoints/{endpoint_id}")


# ---------------------------------------------------------------------------
# 2. Initiatives (CRUD, brouillons & disponibilité des champs)
# ---------------------------------------------------------------------------


@mcp.tool()
async def idhall_list_ideas(
    props: list[str] | None = None,
    filter: dict[str, Any] | None = None,
    offset: int = 0,
    page_size: int = 20,
    count: bool = False,
) -> dict[str, Any]:
    """Liste les initiatives IDhall avec pagination, projection (`props`) et filtres (`filter`).

    Args:
        props: Propriétés à inclure (ex: ["title", "description", "plan", "stage", "author"]).
        filter: Filtre structuré conforme à `IdeaFilter` (ex: {"plan": 1, "title": "Qualité"}).
        offset: Index de départ (>= 0).
        page_size: Nombre d'éléments par page (1 à 100, défaut 20).
        count: Si True, inclut le nombre total de résultats.
    """
    return await _get_client().request(
        "GET",
        "/api/v1/ideas",
        query_params={
            "props": props,
            "filter": filter,
            "offset": offset,
            "page_size": max(1, min(page_size, 100)),
            "count": count,
        },
    )


@mcp.tool()
async def idhall_count_ideas(filter: dict[str, Any] | None = None) -> dict[str, Any]:
    """Compte le nombre d'initiatives correspondant au filtre donné (`IdeaFilter`)."""
    return await _get_client().request(
        "GET", "/api/v1/ideas/count", query_params={"filter": filter} if filter else None
    )


@mcp.tool()
async def idhall_get_idea(idea_id: int, props: list[str] | None = None) -> dict[str, Any]:
    """Récupère les détails d'une initiative par son ID. Passez `props` pour obtenir plus que {id, title}."""
    return await _get_client().request(
        "GET", f"/api/v1/ideas/{idea_id}", query_params={"props": props} if props else None
    )


@mcp.tool()
async def idhall_get_idea_input_availability(
    idea_id: int | None = None,
    plan_id: int | None = None,
) -> dict[str, Any]:
    """Retourne les propriétés disponibles/requises pour créer (idea_id=None) ou modifier une initiative."""
    if idea_id is None:
        return await _get_client().request(
            "GET",
            "/api/v1/ideas/post-input-availability",
            query_params={"plan": plan_id} if plan_id is not None else None,
        )
    return await _get_client().request("GET", f"/api/v1/ideas/{idea_id}/patch-input-availability")


@mcp.tool()
async def idhall_create_idea(
    title: str,
    plan: int,
    description: str | None = None,
    context: str | None = None,
    extra_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Crée et publie immédiatement une nouvelle initiative dans IDhall (`POST /api/v1/ideas`).

    Args:
        title: Intitulé de l'initiative (max 150 caractères).
        plan: Identifiant numérique de l'axe (`plan`) cible.
        description: Description de l'initiative.
        context: Contexte de l'initiative.
        extra_fields: Champs additionnels optionnels (ex: targeted_sites, targeted_organizations, categories, author, etc.).
    """
    payload: dict[str, Any] = {"title": title, "plan": plan}
    if description is not None:
        payload["description"] = description
    if context is not None:
        payload["context"] = context
    if extra_fields:
        payload.update(extra_fields)
    return await _get_client().request("POST", "/api/v1/ideas", json_body=payload)


@mcp.tool()
async def idhall_create_idea_draft(
    title: str,
    plan: int | None = None,
    description: str | None = None,
    extra_fields: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Crée une initiative à l'état brouillon (`POST /api/v1/ideas/draft`)."""
    payload: dict[str, Any] = {"title": title}
    if plan is not None:
        payload["plan"] = plan
    if description is not None:
        payload["description"] = description
    if extra_fields:
        payload.update(extra_fields)
    return await _get_client().request("POST", "/api/v1/ideas/draft", json_body=payload)


@mcp.tool()
async def idhall_publish_idea_draft(
    idea_id: int,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Publie une initiative brouillon existante (`POST /api/v1/ideas/{id}/publish`)."""
    return await _get_client().request("POST", f"/api/v1/ideas/{idea_id}/publish", json_body=payload)


@mcp.tool()
async def idhall_update_idea(idea_id: int, fields: dict[str, Any]) -> dict[str, Any]:
    """Modifie partiellement une initiative existante (`PATCH /api/v1/ideas/{id}`).

    Ne passez dans `fields` que les propriétés à modifier.
    """
    return await _get_client().request("PATCH", f"/api/v1/ideas/{idea_id}", json_body=fields)


@mcp.tool()
async def idhall_delete_idea(idea_id: int) -> dict[str, Any]:
    """Supprime définitivement une initiative (`DELETE /api/v1/ideas/{id}`)."""
    return await _get_client().request("DELETE", f"/api/v1/ideas/{idea_id}")


# ---------------------------------------------------------------------------
# 3. Workflow / Traitement des initiatives
# ---------------------------------------------------------------------------


@mcp.tool()
async def idhall_get_idea_stage(idea_id: int, props: list[str] | None = None) -> dict[str, Any]:
    """Retourne l'étape de traitement en cours d'une initiative (`GET /api/v1/ideas/{id}/stages/current`)."""
    return await _get_client().request(
        "GET",
        f"/api/v1/ideas/{idea_id}/stages/current",
        query_params={"props": props} if props else None,
    )


@mcp.tool()
async def idhall_transition_idea_stage(
    idea_id: int,
    action: STAGE_TRANSITIONS,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fait avancer ou annule l'étape de traitement d'une initiative.

    Actions supportées :
    - `standby`, `change-approver`, `request-details`, `request-expertise`
    - `approve--request-implementation-schedule`, `approve--launch-implementation`, `approve--end-implementation`
    - `reject`, `end-implementation`, `close`
    - `cancel` (annule la dernière étape via `DELETE /api/v1/ideas/{id}/stages/current`)
    """
    if action == "cancel":
        return await _get_client().request("DELETE", f"/api/v1/ideas/{idea_id}/stages/current")
    return await _get_client().request(
        "POST", f"/api/v1/ideas/{idea_id}/stages/{action}", json_body=payload
    )


# ---------------------------------------------------------------------------
# 4. Mise en œuvre & Plan d'action
# ---------------------------------------------------------------------------


@mcp.tool()
async def idhall_get_idea_implementation(
    idea_id: int,
    props: list[str] | None = None,
) -> dict[str, Any]:
    """Récupère les informations de mise en œuvre d'une initiative."""
    return await _get_client().request(
        "GET",
        f"/api/v1/ideas/{idea_id}/implementation",
        query_params={"props": props} if props else None,
    )


@mcp.tool()
async def idhall_update_idea_implementation_progress(
    idea_id: int,
    percent: int | None = None,
    confidence: str | None = None,
    comment: str | None = None,
) -> dict[str, Any]:
    """Met à jour l'état d'avancement de la mise en œuvre d'une initiative."""
    body: dict[str, Any] = {}
    if percent is not None:
        body["percent"] = percent
    if confidence is not None:
        body["confidence"] = confidence
    if comment is not None:
        body["comment"] = comment
    return await _get_client().request(
        "POST", f"/api/v1/ideas/{idea_id}/implementation/progress", json_body=body
    )


@mcp.tool()
async def idhall_list_action_plan_tasks(
    idea_id: int,
    props: list[str] | None = None,
) -> dict[str, Any]:
    """Liste les tâches du plan d'action d'une initiative."""
    return await _get_client().request(
        "GET",
        f"/api/v1/ideas/{idea_id}/action-plan/tasks",
        query_params={"props": props} if props else None,
    )


@mcp.tool()
async def idhall_create_action_plan_task(
    idea_id: int,
    title: str,
    owner: int | None = None,
    description: str | None = None,
    phase: int | None = None,
    section: str | None = None,
    time_range: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Ajoute une tâche au plan d'action d'une initiative (`POST /api/v1/ideas/{id}/action-plan/tasks`)."""
    body: dict[str, Any] = {"title": title}
    if owner is not None:
        body["owner"] = owner
    if description is not None:
        body["description"] = description
    if phase is not None:
        body["phase"] = phase
    if section is not None:
        body["section"] = section
    if time_range is not None:
        body["time_range"] = time_range
    return await _get_client().request(
        "POST", f"/api/v1/ideas/{idea_id}/action-plan/tasks", json_body=body
    )


@mcp.tool()
async def idhall_update_action_plan_task(
    idea_id: int,
    task_id: int,
    fields: dict[str, Any],
) -> dict[str, Any]:
    """Modifie une tâche d'un plan d'action (`PATCH /api/v1/ideas/{id}/action-plan/tasks/{task_id}`)."""
    return await _get_client().request(
        "PATCH", f"/api/v1/ideas/{idea_id}/action-plan/tasks/{task_id}", json_body=fields
    )


@mcp.tool()
async def idhall_update_task_progress(
    idea_id: int,
    task_id: int,
    percent: int | None = None,
    confidence: str | None = None,
    comment: str | None = None,
) -> dict[str, Any]:
    """Met à jour l'avancement d'une tâche d'un plan d'action."""
    body: dict[str, Any] = {}
    if percent is not None:
        body["percent"] = percent
    if confidence is not None:
        body["confidence"] = confidence
    if comment is not None:
        body["comment"] = comment
    return await _get_client().request(
        "POST",
        f"/api/v1/ideas/{idea_id}/action-plan/tasks/{task_id}/progress",
        json_body=body,
    )


@mcp.tool()
async def idhall_delete_action_plan_task(idea_id: int, task_id: int) -> dict[str, Any]:
    """Supprime une tâche d'un plan d'action (`DELETE /api/v1/ideas/{id}/action-plan/tasks/{task_id}`)."""
    return await _get_client().request(
        "DELETE", f"/api/v1/ideas/{idea_id}/action-plan/tasks/{task_id}"
    )


# ---------------------------------------------------------------------------
# 5. Collaboration (Contributions, Mémo, Tags, Analyse d'opportunité)
# ---------------------------------------------------------------------------


@mcp.tool()
async def idhall_list_idea_contributions(
    idea_id: int,
    props: list[str] | None = None,
) -> dict[str, Any]:
    """Liste les contributions d'une initiative."""
    return await _get_client().request(
        "GET",
        f"/api/v1/ideas/{idea_id}/contributions",
        query_params={"props": props} if props else None,
    )


@mcp.tool()
async def idhall_add_idea_contribution(
    idea_id: int,
    text: str,
    sentiment: str | None = None,
) -> dict[str, Any]:
    """Ajoute une contribution (commentaire) à une initiative."""
    body: dict[str, Any] = {"text": text}
    if sentiment is not None:
        body["sentiment"] = sentiment
    return await _get_client().request(
        "POST", f"/api/v1/ideas/{idea_id}/contributions", json_body=body
    )


@mcp.tool()
async def idhall_get_idea_memo(idea_id: int) -> dict[str, Any]:
    """Récupère le mémo d'une initiative."""
    return await _get_client().request("GET", f"/api/v1/ideas/{idea_id}/memo")


@mcp.tool()
async def idhall_set_idea_memo(idea_id: int, memo: str) -> dict[str, Any]:
    """Définit ou remplace le mémo d'une initiative (`PUT /api/v1/ideas/{id}/memo`)."""
    return await _get_client().request("PUT", f"/api/v1/ideas/{idea_id}/memo", json_body={"memo": memo})


@mcp.tool()
async def idhall_get_idea_tags(idea_id: int) -> dict[str, Any]:
    """Récupère les tags associés à une initiative."""
    return await _get_client().request("GET", f"/api/v1/ideas/{idea_id}/tags")


@mcp.tool()
async def idhall_manage_idea_tags(
    idea_id: int,
    operation: Literal["add", "replace", "remove"],
    tags: list[str],
) -> dict[str, Any]:
    """Ajoute (`add`), remplace (`replace`) ou supprime (`remove`) des tags sur une initiative."""
    method_map = {"add": "POST", "replace": "PUT", "remove": "DELETE"}
    return await _get_client().request(
        method_map[operation], f"/api/v1/ideas/{idea_id}/tags", json_body={"tags": tags}
    )


@mcp.tool()
async def idhall_get_opportunity_analysis(
    idea_id: int,
    props: list[str] | None = None,
) -> dict[str, Any]:
    """Récupère l'analyse d'opportunité d'une initiative."""
    return await _get_client().request(
        "GET",
        f"/api/v1/ideas/{idea_id}/opportunity-analysis",
        query_params={"props": props} if props else None,
    )


# ---------------------------------------------------------------------------
# 6. Utilisateurs & Référentiels
# ---------------------------------------------------------------------------


@mcp.tool()
async def idhall_list_users(
    props: list[str] | None = None,
    filter: dict[str, Any] | None = None,
    offset: int = 0,
    page_size: int = 20,
    count: bool = False,
) -> dict[str, Any]:
    """Liste les utilisateurs IDhall avec pagination, projection (`props`) et filtres (`UserFilter`)."""
    return await _get_client().request(
        "GET",
        "/api/v1/users",
        query_params={
            "props": props,
            "filter": filter,
            "offset": offset,
            "page_size": max(1, min(page_size, 100)),
            "count": count,
        },
    )


@mcp.tool()
async def idhall_get_user(user_id: int, props: list[str] | None = None) -> dict[str, Any]:
    """Récupère la fiche d'un utilisateur IDhall par son ID."""
    return await _get_client().request(
        "GET", f"/api/v1/users/{user_id}", query_params={"props": props} if props else None
    )


@mcp.tool()
async def idhall_list_reference_items(
    resource: REFERENCE_RESOURCES,
    props: list[str] | None = None,
    filter: dict[str, Any] | None = None,
    offset: int = 0,
    page_size: int = 50,
    count: bool = False,
) -> dict[str, Any]:
    """Liste les éléments d'un référentiel IDhall (plans, sites, organizations, categories, risks, stakeholders, etc.)."""
    query: dict[str, Any] = {}
    if resource != "countries":
        query = {
            "props": props,
            "filter": filter,
            "offset": offset,
            "page_size": max(1, min(page_size, 100)),
            "count": count,
        }
    return await _get_client().request("GET", f"/api/v1/{resource}", query_params=query or None)


# ---------------------------------------------------------------------------
# 7. Outil universel pour couvrir 100 % des 208 endpoints
# ---------------------------------------------------------------------------


@mcp.tool()
async def idhall_api_request(
    method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"],
    path: str,
    query_params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
) -> Any:
    """Exécute un appel arbitraire vers n'importe lequel des 208 endpoints de l'API REST IDhall v1.

    Avant d'utiliser cet outil sur un endpoint spécialisé (ex: audits, parties prenantes/contacts,
    ressources/pièces jointes, critères d'opportunité, lots de plan d'action), consultez son schéma
    avec `idhall_search_endpoints` et `idhall_get_endpoint_spec`.

    Args:
        method: Méthode HTTP (`GET`, `POST`, `PUT`, `PATCH`, `DELETE`).
        path: Chemin relatif, ex: `/api/v1/stakeholders/12/contacts` ou `risks/1`.
        query_params: Paramètres de requête (ex: `{"props": ["title", "description"], "page_size": 10}`).
        json_body: Corps JSON pour `POST`/`PUT`/`PATCH` (ou filtres complexes).
    """
    return await _get_client().request(
        method, path, query_params=query_params, json_body=json_body
    )


# ---------------------------------------------------------------------------
# Healthcheck HTTP (Docker / Reverse Proxy / Kubernetes)
# ---------------------------------------------------------------------------


@mcp.custom_route("/health", methods=["GET"])
async def health_check(_request: Request) -> JSONResponse:
    """Endpoint de santé léger (sans authentification) pour Docker HEALTHCHECK et reverse proxies."""
    return JSONResponse({"status": "ok", "service": "mcp-idhall", "version": __version__})


# ---------------------------------------------------------------------------
# Point d'entrée CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Serveur MCP FastMCP pour l'API REST IDhall v1")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http", "sse"],
        default=os.environ.get("MCP_TRANSPORT", "stdio"),
        help="Transport MCP : 'stdio' (local) ou 'streamable-http' / 'sse' (multi-utilisateurs HTTP).",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("MCP_HOST", "127.0.0.1"),
        help="Adresse d'écoute HTTP (défaut: MCP_HOST ou 127.0.0.1)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("MCP_PORT", "8000")),
        help="Port d'écoute HTTP (défaut: MCP_PORT ou 8000)",
    )
    parser.add_argument(
        "--load-dotenv",
        action="store_true",
        help="Charge le fichier .env local (utile en mode stdio dev ; évité par défaut en mode HTTP multi-utilisateurs).",
    )
    args = parser.parse_args()

    # En mode stdio, on charge .env automatiquement s'il existe ; en mode HTTP multi-utilisateurs,
    # on ne le charge que si --load-dotenv est explicitement demandé pour éviter tout partage involontaire de jeton.
    if args.transport == "stdio" or args.load_dotenv:
        load_dotenv()

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
