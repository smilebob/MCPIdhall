#!/usr/bin/env python3
"""Generate docs/openapi.json (OpenAPI 3.1.0) and docs/IDHALL_API_SYNTHESE.md
from docs/idhall_api_reference.json.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = ROOT / "docs" / "idhall_api_reference.json"
OPENAPI_PATH = ROOT / "docs" / "openapi.json"
SYNTHESE_PATH = ROOT / "docs" / "IDHALL_API_SYNTHESE.md"


DOMAIN_LABELS: dict[str, str] = {
    "about": "À propos de l'API",
    "reference": "Référentiel de l'API",
    "locale-settings": "Paramètres régionaux",
    "countries": "Pays",
    "ideas": "Initiatives",
    "ideas:opportunity-analysis": "Initiatives — Analyse d'opportunité",
    "ideas:implementation": "Initiatives — Mise en œuvre",
    "ideas:action-plan": "Initiatives — Plan d'action",
    "ideas:stages": "Initiatives — Traitement (Workflow)",
    "ideas:contributions": "Initiatives — Contributions",
    "ideas:audits": "Initiatives — Vérifications d'efficacité",
    "ideas:memo": "Initiatives — Mémo",
    "ideas:tags": "Initiatives — Tags",
    "idea-submission-guidances": "Aides à la déclaration d'initiatives",
    "idea-rejection-reasons": "Motifs de non-recevabilité",
    "idea-selections": "Sélections d'initiatives",
    "action-plan-templates": "Modèles de plan d'action",
    "phases-templates": "Plans de phases",
    "plans": "Axes",
    "perspectives": "Perspectives",
    "categories": "Catégories",
    "classes": "Typologies",
    "events": "Évènements générateurs",
    "event-types": "Types d'évènement",
    "organizations": "Services",
    "sites": "Sites",
    "processes": "Processus",
    "products": "Produits",
    "risks": "Risques",
    "risk-types": "Types de risque",
    "stakeholders": "Parties prenantes",
    "stakeholder-types": "Types de partie prenante",
    "eval-scales": "Échelles de mesure",
    "eval-units": "Unités de mesure",
    "users": "Utilisateurs",
    "user-profiles": "Profils d'accès",
    "user-registration-requests": "Demandes d'inscription",
}


def classify_tag(path: str) -> str:
    rel = re.sub(r"^/api/v1/", "", path).strip("/")
    parts = rel.split("/")
    if not parts:
        return "Autres"
    root = parts[0]
    if root == "ideas" and len(parts) >= 3 and parts[1].startswith("{"):
        sub = parts[2]
        key = f"ideas:{sub}"
        if key in DOMAIN_LABELS:
            return DOMAIN_LABELS[key]
    return DOMAIN_LABELS.get(root, root)


def strip_base(url: str, base_url: str) -> str:
    if url.startswith(base_url):
        return url[len(base_url) :]
    m = re.match(r"^https?://[^/]+(/.*)$", url)
    return m.group(1) if m else url


def convert_type(type_obj: dict[str, Any] | None, known_classes: set[str]) -> dict[str, Any]:
    if not isinstance(type_obj, dict):
        return {"type": "string"}

    name = str(type_obj.get("name", "string")).strip()
    schema: dict[str, Any] = {}

    # Array suffix e.g. "string[]", "integer[]", "object(Foo)[]"
    if name.endswith("[]"):
        inner_name = name[:-2]
        inner_obj = dict(type_obj)
        inner_obj["name"] = inner_name
        inner_obj.pop("description", None)
        schema = {"type": "array", "items": convert_type(inner_obj, known_classes)}
    else:
        m_obj = re.match(r"^object\(([^)]+)\)$", name)
        if m_obj:
            cls_name = m_obj.group(1).strip()
            if cls_name in known_classes:
                schema = {"$ref": f"#/components/schemas/{cls_name}"}
            else:
                schema = {"type": "object", "title": cls_name}
        elif name in ("string", "text", "html", "email", "url", "uri", "uuid"):
            schema = {"type": "string"}
            if name in ("email", "uri", "uuid"):
                schema["format"] = name
        elif name in ("integer", "int"):
            schema = {"type": "integer"}
        elif name in ("float", "double", "decimal", "number"):
            schema = {"type": "number"}
        elif name in ("boolean", "bool"):
            schema = {"type": "boolean"}
        elif name == "date":
            schema = {"type": "string", "format": "date"}
        elif name in ("datetime", "date-time", "timestamp"):
            schema = {"type": "string", "format": "date-time"}
        elif name in ("file", "binary"):
            schema = {"type": "string", "format": "binary"}
        elif name == "array":
            schema = {"type": "array", "items": {}}
        elif name == "object":
            schema = {"type": "object"}
            if isinstance(type_obj.get("properties"), list):
                props, req = convert_properties(type_obj["properties"], known_classes)
                schema["properties"] = props
                if req:
                    schema["required"] = req
        elif name == "mixed" or name == "any":
            schema = {}
        else:
            schema = {"type": "string", "x-idhall-type": name}

    # Add constraints if not a $ref
    if "$ref" not in schema:
        if "min_value" in type_obj and type_obj["min_value"] is not None:
            schema["minimum"] = type_obj["min_value"]
        if "max_value" in type_obj and type_obj["max_value"] is not None:
            schema["maximum"] = type_obj["max_value"]
        if "min_length" in type_obj and type_obj["min_length"] is not None:
            schema["minLength"] = type_obj["min_length"]
        if "max_length" in type_obj and type_obj["max_length"] is not None:
            schema["maxLength"] = type_obj["max_length"]
        for enum_key in ("allowed_values", "values", "enum"):
            vals = type_obj.get(enum_key)
            if isinstance(vals, list) and vals:
                if all(isinstance(v, dict) and "value" in v for v in vals):
                    schema["enum"] = [v["value"] for v in vals]
                elif all(not isinstance(v, (dict, list)) for v in vals):
                    schema["enum"] = vals
                break
        if "description" in type_obj and type_obj["description"]:
            schema["description"] = type_obj["description"]
        if "details" in type_obj and type_obj["details"]:
            prev = schema.get("description", "")
            schema["description"] = (f"{prev} {type_obj['details']}").strip()

    return schema


def convert_param_schema(param: dict[str, Any], known_classes: set[str]) -> dict[str, Any]:
    primary = convert_type(param.get("type"), known_classes)
    alt_types = param.get("alt_types")
    if isinstance(alt_types, list) and alt_types:
        variants = [primary]
        for alt in alt_types:
            alt_schema = convert_type(alt.get("type"), known_classes)
            if alt.get("description") and "$ref" not in alt_schema and "description" not in alt_schema:
                alt_schema["description"] = alt["description"]
            if alt_schema not in variants:
                variants.append(alt_schema)
        schema: dict[str, Any] = {"oneOf": variants} if len(variants) > 1 else primary
    else:
        schema = primary

    if "$ref" not in schema:
        if param.get("description") and "description" not in schema:
            schema["description"] = param["description"]
        if "default_value" in param and param["default_value"] is not None:
            schema["default"] = param["default_value"]
    return schema


def convert_properties(
    prop_list: list[dict[str, Any]], known_classes: set[str]
) -> tuple[dict[str, Any], list[str]]:
    props: dict[str, Any] = {}
    required: list[str] = []
    for p in prop_list:
        pname = p.get("name")
        if not pname:
            continue
        props[pname] = convert_param_schema(p, known_classes)
        if p.get("required") is True:
            required.append(pname)
    return props, required


def collect_classes(details: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    raw_classes: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for ep in details.values():
        for cls in ep.get("classes") or []:
            cname = cls.get("name")
            if not cname:
                continue
            for prop in cls.get("properties") or []:
                pname = prop.get("name")
                if pname and pname not in raw_classes[cname]:
                    raw_classes[cname][pname] = prop

    known = set(raw_classes.keys())
    schemas: dict[str, dict[str, Any]] = {
        "ProblemDetails": {
            "type": "object",
            "description": "Réponse d'erreur RFC 7807 (application/problem+json) retournée par IDhall.",
            "properties": {
                "title": {"type": "string"},
                "severity": {"type": "string"},
                "issuer": {"type": "string"},
                "issue_type": {"type": "string"},
                "issue_code": {"type": "integer"},
                "status": {"type": "integer"},
                "detail": {"type": "string"},
            },
        }
    }

    for cname in sorted(known):
        props_list = list(raw_classes[cname].values())
        props, req = convert_properties(props_list, known)
        s: dict[str, Any] = {"type": "object", "properties": props}
        if req:
            s["required"] = req
        schemas[cname] = s

    return schemas


def build_openapi(raw: dict[str, Any]) -> dict[str, Any]:
    base_url = raw["base_url"].rstrip("/")
    about = raw.get("about", {})
    app_ver = about.get("app", {}).get("version", "5.0")
    api_ver = about.get("api", {}).get("version", "1")
    details: dict[str, dict[str, Any]] = raw["endpoint_details"]
    index: list[dict[str, Any]] = raw["endpoints_index"]

    schemas = collect_classes(details)
    known_classes = set(schemas.keys())

    paths: dict[str, dict[str, Any]] = {}
    used_tags: set[str] = set()

    for entry in index:
        ep_id = entry["link"].rsplit("/", 1)[-1]
        ep = details.get(ep_id)
        if not ep:
            continue

        method = ep["method"].lower()
        path = strip_base(ep["url"], base_url)
        tag = classify_tag(path)
        used_tags.add(tag)

        parameters: list[dict[str, Any]] = []

        # Path parameters
        for pp in ep.get("path_params") or []:
            raw_name = str(pp.get("name", "")).strip("{}")
            parameters.append(
                {
                    "name": raw_name,
                    "in": "path",
                    "required": True,
                    "description": pp.get("description", ""),
                    "schema": convert_param_schema(pp, known_classes),
                }
            )

        # Header parameters (skip Authorization, handled by securityScheme)
        for hp in ep.get("request_headers") or []:
            hname = hp.get("name", "")
            if not hname or hname.lower() == "authorization":
                continue
            parameters.append(
                {
                    "name": hname,
                    "in": "header",
                    "required": bool(hp.get("required", False)),
                    "description": hp.get("description", ""),
                    "schema": convert_param_schema(hp, known_classes),
                }
            )

        # Query parameters
        for qp in ep.get("request_query_params") or []:
            qname = qp.get("name", "")
            if not qname:
                continue
            parameters.append(
                {
                    "name": qname,
                    "in": "query",
                    "required": bool(qp.get("required", False)),
                    "description": qp.get("description", ""),
                    "schema": convert_param_schema(qp, known_classes),
                }
            )

        op: dict[str, Any] = {
            "operationId": ep_id,
            "summary": ep.get("title", ep_id),
            "tags": [tag],
        }
        if ep.get("description"):
            op["description"] = ep["description"]
        if parameters:
            op["parameters"] = parameters

        # Request body
        payload_formats = ep.get("request_payload_formats")
        if isinstance(payload_formats, list) and payload_formats:
            content: dict[str, Any] = {}
            for fmt in payload_formats:
                cts = fmt.get("content_types") or ["application/json"]
                if isinstance(cts, str):
                    cts = [cts]
                params_list = fmt.get("params") or []
                if params_list:
                    props, req = convert_properties(params_list, known_classes)
                    body_schema: dict[str, Any] = {"type": "object", "properties": props}
                    if req:
                        body_schema["required"] = req
                else:
                    body_schema = {"type": "object"}
                for ct in cts:
                    content[ct] = {"schema": body_schema}
            rb: dict[str, Any] = {"content": content}
            if ep.get("request_payload_description"):
                rb["description"] = ep["request_payload_description"]
            op["requestBody"] = rb

        # Responses
        def_resp = ep.get("default_response") or {}
        http_code = str(def_resp.get("http_code", 200))
        resp_obj: dict[str, Any] = {
            "description": def_resp.get("content_description") or "Succès",
        }
        ct = def_resp.get("content_type")
        if ct and http_code != "204":
            cprops = def_resp.get("content_properties")
            if isinstance(cprops, list) and cprops:
                r_props, _ = convert_properties(cprops, known_classes)
                r_schema: dict[str, Any] = {"type": "object", "properties": r_props}
            else:
                # Try to infer referenced class from content_description
                desc = def_resp.get("content_description", "")
                m_cls = re.search(r"type\s+([A-Z][A-Za-z0-9_]+)", desc)
                if m_cls and m_cls.group(1) in known_classes:
                    r_schema = {"$ref": f"#/components/schemas/{m_cls.group(1)}"}
                else:
                    r_schema = {"type": "object"}
            resp_obj["content"] = {ct: {"schema": r_schema}}

        responses: dict[str, Any] = {
            http_code: resp_obj,
            "400": {
                "description": "Requête invalide",
                "content": {"application/problem+json": {"schema": {"$ref": "#/components/schemas/ProblemDetails"}}},
            },
            "401": {
                "description": "Non authentifié (jeton JWT manquant ou invalide)",
                "content": {"application/problem+json": {"schema": {"$ref": "#/components/schemas/ProblemDetails"}}},
            },
            "403": {
                "description": "Accès refusé (permissions insuffisantes)",
                "content": {"application/problem+json": {"schema": {"$ref": "#/components/schemas/ProblemDetails"}}},
            },
            "404": {
                "description": "Ressource ou service introuvable",
                "content": {"application/problem+json": {"schema": {"$ref": "#/components/schemas/ProblemDetails"}}},
            },
            "429": {"description": "Trop de requêtes (Rate Limit Apache)"},
        }
        op["responses"] = responses

        paths.setdefault(path, {})[method] = op

    openapi: dict[str, Any] = {
        "openapi": "3.1.0",
        "info": {
            "title": "IDhall REST API (Humanperf Software)",
            "version": f"v{api_ver} (IDhall {app_ver})",
            "description": (
                "Spécification OpenAPI 3.1.0 générée automatiquement depuis le référentiel "
                "d'introspection officiel de l'API REST IDhall (/api/v1/reference/endpoints)."
            ),
        },
        "servers": [{"url": base_url, "description": "Instance IDhall"}],
        "security": [{"bearerAuth": []}],
        "tags": [{"name": t} for t in sorted(used_tags)],
        "paths": dict(sorted(paths.items())),
        "components": {
            "securitySchemes": {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "Jeton JWT RS256 généré dans IDhall (Mon compte > Connexion et sécurité).",
                }
            },
            "schemas": schemas,
        },
    }
    return openapi


def build_synthese(raw: dict[str, Any], openapi: dict[str, Any]) -> str:
    base_url = raw["base_url"].rstrip("/")
    about = raw.get("about", {})
    app_ver = about.get("app", {}).get("version", "?")
    api_ver = about.get("api", {}).get("version", "1")
    details = raw["endpoint_details"]
    index = raw["endpoints_index"]
    schemas = openapi["components"]["schemas"]

    # Group endpoints by tag
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    method_counts: dict[str, int] = defaultdict(int)
    for entry in index:
        ep_id = entry["link"].rsplit("/", 1)[-1]
        ep = details.get(ep_id)
        if not ep:
            continue
        path = strip_base(ep["url"], base_url)
        tag = classify_tag(path)
        method = ep["method"].upper()
        method_counts[method] += 1
        grouped[tag].append(
            {
                "id": ep_id,
                "method": method,
                "path": path,
                "title": ep.get("title", ""),
                "http_code": (ep.get("default_response") or {}).get("http_code", ""),
                "query_params": [q["name"] for q in (ep.get("request_query_params") or []) if "name" in q],
                "payload_params": [
                    p["name"] + ("*" if p.get("required") else "")
                    for fmt in (ep.get("request_payload_formats") or [])
                    for p in (fmt.get("params") or [])
                    if "name" in p
                ],
            }
        )

    lines: list[str] = []
    lines.append("# Synthèse complète — API REST IDhall (Humanperf Software)\n")
    lines.append(f"- **Instance :** `{base_url}`")
    lines.append(f"- **Version IDhall :** `{app_ver}` (`version_number`: `{about.get('app', {}).get('version_number')}`)")
    lines.append(f"- **Version API :** `v{api_ver}`")
    lines.append(f"- **Total endpoints documentés :** **{len(index)}**")
    lines.append(
        "- **Répartition par méthode HTTP :** "
        + ", ".join(f"`{m}` : {c}" for m, c in sorted(method_counts.items()))
    )
    lines.append(f"- **Modèles / Classes typées :** **{len(schemas) - 1}** (+ `ProblemDetails`)")
    lines.append(f"- **Export généré le :** `{raw.get('exported_at')}`\n")

    lines.append("---\n")
    lines.append("## 1. Conventions techniques transverses\n")
    lines.append("### Authentification & En-têtes")
    lines.append("- `Authorization: Bearer <JWT>` *(obligatoire)* — Jeton JWT signé (`RS256`), lié à un utilisateur IDhall dont il hérite strictement les permissions.")
    lines.append("- `Accept: application/json`")
    lines.append("- `Accept-Language` *(optionnel, ex. `fr`, `en`)* — Langue des libellés et messages d'erreur.")
    lines.append("- `IDhall-Timezone` *(optionnel)* — Fuseau horaire (liste via `GET /api/v1/locale-settings/timezones`).\n")

    lines.append("### Pagination, Projection (`props`) et Filtres (`filter`)")
    lines.append("- **Pagination :** `offset` (défaut `0`), `page_size` (`1` à `100`, défaut `20`), `count` (`true`/`false` pour inclure le total dans la réponse). Chaque collection dispose aussi d'un endpoint dédié `GET .../count`.")
    lines.append("- **Projection des champs (`props`) :** Par défaut, les endpoints `GET` ne retournent que les champs minimaux (`id`, `title`, etc.). Passez `props` (tableau `props[]=...` ou liste séparée par des espaces) pour sélectionner les propriétés voulues.")
    lines.append("- **Filtres (`filter`) :** Objet structuré (ex. `IdeaFilter`, `UserFilter`, etc.). Sur la plupart des endpoints `GET`, les paramètres de requête peuvent aussi être envoyés dans le **corps de la requête** (`application/json`, `application/x-www-form-urlencoded`, `multipart/form-data`).")
    lines.append("- **Erreurs :** Format standard RFC 7807 `application/problem+json` (`title`, `severity`, `issuer`, `issue_type`, `issue_code`, `status`).")
    lines.append("- **Rate Limiting :** Limitation de débit active côté serveur (`HTTP 429 Too Many Requests`). Prévoir un backoff exponentiel côté client / serveur MCP.\n")

    lines.append("---\n")
    lines.append("## 2. Vue d'ensemble par domaine\n")
    lines.append("| Domaine | Endpoints | Méthodes |")
    lines.append("| :--- | :---: | :--- |")
    for tag in sorted(grouped.keys()):
        eps = grouped[tag]
        ms = sorted({e["method"] for e in eps})
        lines.append(f"| {tag} | {len(eps)} | {', '.join(f'`{m}`' for m in ms)} |")
    lines.append("")

    lines.append("---\n")
    lines.append("## 3. Catalogue complet des 208 endpoints\n")
    for tag in sorted(grouped.keys()):
        eps = grouped[tag]
        lines.append(f"### {tag} ({len(eps)})\n")
        lines.append("| Méthode | Chemin | Description | Paramètres / Payload (`*` = requis) | Code |")
        lines.append("| :--- | :--- | :--- | :--- | :---: |")
        for e in sorted(eps, key=lambda x: (x["path"], x["method"])):
            params_parts = []
            if e["query_params"]:
                params_parts.append("Query: " + ", ".join(f"`{p}`" for p in e["query_params"][:6]))
            if e["payload_params"]:
                shown = e["payload_params"][:8]
                more = f" (+{len(e['payload_params']) - 8})" if len(e["payload_params"]) > 8 else ""
                params_parts.append("Body: " + ", ".join(f"`{p}`" for p in shown) + more)
            params_str = " ; ".join(params_parts) if params_parts else "—"
            title = e["title"].replace("|", "\\|")
            lines.append(f"| `{e['method']}` | `{e['path']}` | {title} | {params_str} | `{e['http_code']}` |")
        lines.append("")

    lines.append("---\n")
    lines.append("## 4. Modèles de données principaux (`components.schemas`)\n")
    lines.append(f"La spécification OpenAPI complète (`docs/openapi.json`) définit **{len(schemas)} schémas**.\n")
    lines.append("| Modèle | Nb propriétés | Aperçu des propriétés |")
    lines.append("| :--- | :---: | :--- |")
    for cname, cschema in sorted(schemas.items()):
        cprops = list((cschema.get("properties") or {}).keys())
        preview = ", ".join(f"`{p}`" for p in cprops[:10])
        if len(cprops) > 10:
            preview += f", … (+{len(cprops) - 10})"
        lines.append(f"| `{cname}` | {len(cprops)} | {preview} |")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
    openapi = build_openapi(raw)
    OPENAPI_PATH.write_text(json.dumps(openapi, ensure_ascii=False, indent=2), encoding="utf-8")
    synthese = build_synthese(raw, openapi)
    SYNTHESE_PATH.write_text(synthese, encoding="utf-8")
    print(
        f"Generated:\n"
        f"  - {OPENAPI_PATH} ({len(openapi['paths'])} paths, {len(openapi['components']['schemas'])} schemas)\n"
        f"  - {SYNTHESE_PATH} ({len(synthese.splitlines())} lines)"
    )


if __name__ == "__main__":
    main()
