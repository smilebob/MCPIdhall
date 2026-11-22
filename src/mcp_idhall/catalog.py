"""Catalogue local des 208 endpoints IDhall (zéro appel réseau, recherche instantanée)."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

DEFAULT_REF_PATH = Path(__file__).resolve().parent.parent.parent / "docs" / "idhall_api_reference.json"


@lru_cache(maxsize=1)
def _load_reference() -> dict[str, Any]:
    ref_path = Path(os.environ.get("IDHALL_REFERENCE_JSON", str(DEFAULT_REF_PATH)))
    if not ref_path.exists():
        return {"endpoints_index": [], "endpoint_details": {}}
    return json.loads(ref_path.read_text(encoding="utf-8"))


def search_endpoints(
    query: str = "",
    method: str | None = None,
    limit: int = 25,
) -> list[dict[str, str]]:
    """Recherche dans les 208 endpoints documentés par mot-clé et/ou méthode HTTP."""
    data = _load_reference()
    q = query.strip().lower()
    m_filter = method.upper().strip() if method else None
    results: list[dict[str, str]] = []

    for entry in data.get("endpoints_index", []):
        ep_method = str(entry.get("method", "")).upper()
        if m_filter and ep_method != m_filter:
            continue
        title = str(entry.get("title", ""))
        url = str(entry.get("url", ""))
        ep_id = str(entry.get("link", "")).rsplit("/", 1)[-1]
        haystack = f"{ep_method} {url} {title} {ep_id}".lower()
        if q and not all(tok in haystack for tok in q.split()):
            continue
        path = url.split("/api/v1", 1)[-1] if "/api/v1" in url else url
        results.append(
            {
                "endpoint_id": ep_id,
                "method": ep_method,
                "path": f"/api/v1{path}",
                "title": title,
            }
        )
        if len(results) >= max(1, min(limit, 100)):
            break
    return results


def get_endpoint_spec(endpoint_id: str) -> dict[str, Any] | None:
    """Retourne le schéma complet d'un endpoint depuis le référentiel local."""
    data = _load_reference()
    details = data.get("endpoint_details", {})
    if endpoint_id in details:
        return details[endpoint_id]
    # Tolère une recherche insensible à la casse
    target = endpoint_id.strip().lower()
    for k, v in details.items():
        if k.lower() == target:
            return v
    return None
