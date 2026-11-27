"""Client HTTP asynchrone durci pour l'API REST IDhall v1 avec gestion du rate limit (429)."""

from __future__ import annotations

import asyncio
import contextlib
import json
import os
import re
from typing import Any
from urllib.parse import unquote

import httpx

from mcp_idhall.auth import IDhallCredentials

_READ_ONLY_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
_ALLOWED_METHODS = frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"})
_SAFE_PATH_RE = re.compile(r"^/api/v1/[A-Za-z0-9._~/()\-]+$")


class IDhallAPIError(RuntimeError):
    """Erreur structurée retournée par l'API REST IDhall (RFC 7807 ProblemDetails)."""

    def __init__(self, status_code: int, message: str, problem: dict[str, Any] | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.problem = problem or {}


def _is_read_only_mode() -> bool:
    raw = os.environ.get("IDHALL_READ_ONLY", "")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _format_problem(status_code: int, body_text: str) -> IDhallAPIError:
    with contextlib.suppress(json.JSONDecodeError, ValueError):
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
    snippet = body_text.strip()[:300]
    return IDhallAPIError(status_code, f"HTTP {status_code}: {snippet or 'Erreur sans détail'}")


def normalize_api_path(path: str) -> str:
    """Normalise et valide un chemin d'endpoint vers `/api/v1/...` (protection anti-path-traversal)."""
    p = path.strip()
    if not p:
        raise ValueError("Le chemin d'endpoint ne peut pas être vide.")
    if p.startswith(("http://", "https://", "//")):
        raise ValueError(
            "Passez un chemin relatif (ex: '/api/v1/ideas' ou 'ideas'), pas une URL absolue."
        )
    if any(ch in p for ch in ("?", "#", "\\", "@", "\r", "\n", "\x00")):
        raise ValueError(
            "Le chemin d'endpoint contient des caractères interdits (?, #, \\, @ ou caractères de contrôle)."
        )

    decoded = unquote(p)
    if ".." in decoded.split("/") or ".." in p.split("/") or "//" in p:
        raise ValueError("Traversée de chemin ('..' ou '//') interdite dans le chemin d'endpoint.")

    if not p.startswith("/"):
        p = "/" + p
    if not p.startswith("/api/v1/"):
        if p == "/api/v1":
            raise ValueError("Précisez un service après '/api/v1/' (ex: '/api/v1/ideas').")
        if p.startswith("/api/"):
            p = "/api/v1/" + p[len("/api/") :]
        else:
            p = "/api/v1" + p

    if not _SAFE_PATH_RE.match(p):
        raise ValueError(f"Format de chemin d'endpoint invalide : {p!r}")
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
        if norm_method not in _ALLOWED_METHODS:
            raise ValueError(f"Méthode HTTP non supportée : {norm_method!r}")

        if _is_read_only_mode() and norm_method not in _READ_ONLY_METHODS:
            raise IDhallAPIError(
                403,
                f"Mode lecture seule actif (IDHALL_READ_ONLY=true) : méthode {norm_method} bloquée.",
            )

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

        # follow_redirects=False empêche toute fuite de l'en-tête Authorization via redirection 30x
        async with httpx.AsyncClient(
            timeout=self.timeout,
            transport=self._transport,
            follow_redirects=False,
        ) as client:
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
