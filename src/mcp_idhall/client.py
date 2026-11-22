"""Client HTTP asynchrone pour l'API REST IDhall v1 avec gestion du rate limit (429)."""

from __future__ import annotations

import asyncio
import json
from typing import Any

import httpx

from mcp_idhall.auth import IDhallCredentials


class IDhallAPIError(RuntimeError):
    """Erreur structurée retournée par l'API REST IDhall (RFC 7807 ProblemDetails)."""

    def __init__(self, status_code: int, message: str, problem: dict[str, Any] | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.problem = problem or {}


def _format_problem(status_code: int, body_text: str) -> IDhallAPIError:
    try:
        data = json.loads(body_text)
        if isinstance(data, dict):
            title = data.get("title") or f"Erreur HTTP {status_code}"
            detail = data.get("detail") or data.get("issuer") or ""
            code = data.get("issue_code")
            parts = [f"HTTP {status_code}: {title}"]
            if detail:
                parts.append(str(detail))
            if code is not None:
                parts.append(f"(issue_code={code})")
            return IDhallAPIError(status_code, " — ".join(parts), problem=data)
    except Exception:
        pass
    snippet = body_text.strip()[:300]
    return IDhallAPIError(status_code, f"HTTP {status_code}: {snippet or 'Erreur sans détail'}")


def normalize_api_path(path: str) -> str:
    """Normalise un chemin d'endpoint vers `/api/v1/...`."""
    p = path.strip()
    if p.startswith("http://") or p.startswith("https://"):
        raise ValueError("Passez un chemin relatif (ex: '/api/v1/ideas' ou 'ideas'), pas une URL absolue.")
    if not p.startswith("/"):
        p = "/" + p
    if not p.startswith("/api/v1/"):
        if p == "/api/v1":
            p = "/api/v1/"
        elif p.startswith("/api/"):
            p = "/api/v1/" + p[len("/api/") :]
        else:
            p = "/api/v1" + p
    return p


class IDhallClient:
    """Client asynchrone léger et isolé par utilisateur pour l'API IDhall v1."""

    def __init__(
        self,
        credentials: IDhallCredentials,
        *,
        timeout: float = 30.0,
        max_retries: int = 4,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.credentials = credentials
        self.timeout = timeout
        self.max_retries = max_retries
        self._transport = transport

    def _build_headers(self, extra_headers: dict[str, str] | None = None) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.credentials.token}",
            "Accept": "application/json",
            "Accept-Language": self.credentials.language,
        }
        if self.credentials.timezone:
            headers["IDhall-Timezone"] = self.credentials.timezone
        if extra_headers:
            headers.update(extra_headers)
        return headers

    async def request(
        self,
        method: str,
        path: str,
        *,
        query_params: dict[str, Any] | None = None,
        json_body: dict[str, Any] | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> Any:
        """Exécute une requête vers l'API IDhall v1 avec backoff automatique sur 429/5xx."""
        norm_method = method.upper().strip()
        norm_path = normalize_api_path(path)
        url = f"{self.credentials.base_url}{norm_path}"

        params: dict[str, Any] = {}
        body: dict[str, Any] | None = dict(json_body) if json_body is not None else None

        if query_params:
            cleaned_qp = {k: v for k, v in query_params.items() if v is not None}
            has_structured = any(
                isinstance(v, dict) or (isinstance(v, list) and k != "props")
                for k, v in cleaned_qp.items()
            )
            if has_structured or body is not None:
                # IDhall lit soit la query string, soit le corps JSON (pas les deux).
                # Dès qu'un paramètre structuré (ex: filter) ou un body est présent,
                # on place l'ensemble des query_params dans le corps JSON.
                if body is None:
                    body = {}
                for k, v in cleaned_qp.items():
                    body.setdefault(k, v)
            else:
                for k, v in cleaned_qp.items():
                    if k == "props" and isinstance(v, list):
                        params[k] = " ".join(str(x) for x in v if x)
                    elif isinstance(v, bool):
                        params[k] = "true" if v else "false"
                    else:
                        params[k] = v

        headers = self._build_headers(extra_headers)
        backoff = 2.0

        async with httpx.AsyncClient(timeout=self.timeout, transport=self._transport) as client:
            for attempt in range(1, self.max_retries + 1):
                resp = await client.request(
                    norm_method,
                    url,
                    params=params or None,
                    json=body,
                    headers=headers,
                )

                if resp.status_code == 429 or resp.status_code in (502, 503, 504):
                    if attempt < self.max_retries:
                        retry_after = resp.headers.get("Retry-After")
                        wait_s = (
                            float(retry_after)
                            if retry_after and retry_after.replace(".", "", 1).isdigit()
                            else backoff
                        )
                        await asyncio.sleep(min(wait_s, 30.0))
                        backoff = min(backoff * 2.0, 30.0)
                        continue

                if resp.status_code >= 400:
                    raise _format_problem(resp.status_code, resp.text)

                if resp.status_code == 204 or not resp.content:
                    return {"status": resp.status_code, "ok": True}

                content_type = resp.headers.get("content-type", "")
                if "json" in content_type.lower():
                    return resp.json()
                return {"status": resp.status_code, "content_type": content_type, "text": resp.text}

        raise IDhallAPIError(429, "Limite de requêtes atteinte après plusieurs tentatives.")
