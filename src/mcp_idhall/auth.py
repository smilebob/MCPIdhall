"""Authentification JWT par utilisateur et résolution sécurisée de l'URL IDhall."""

from __future__ import annotations

import base64
import json
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from fastmcp.server.dependencies import get_http_headers

DEFAULT_ALLOWED_SUFFIX = ".idhall.com"


class IDhallAuthError(ValueError):
    """Erreur d'authentification ou de configuration de jeton JWT IDhall."""


@dataclass(frozen=True)
class IDhallCredentials:
    """Identifiants résolus pour l'appel courant (strictement isolés par requête)."""

    token: str
    base_url: str
    language: str = "fr"
    timezone: str | None = None
    claims: dict[str, Any] | None = None


def decode_jwt_payload(token: str) -> dict[str, Any]:
    """Décode la partie payload d'un JWT sans vérifier la signature (vérifiée côté IDhall)."""
    parts = token.strip().split(".")
    if len(parts) != 3:
        raise IDhallAuthError(
            "Le jeton fourni n'est pas un JWT valide (3 segments séparés par des points attendus)."
        )
    payload_b64 = parts[1]
    padding = "=" * (-len(payload_b64) % 4)
    try:
        raw = base64.urlsafe_b64decode(payload_b64 + padding)
        data = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise IDhallAuthError(f"Impossible de décoder le payload JWT : {exc}") from exc
    if not isinstance(data, dict):
        raise IDhallAuthError("Le payload JWT décodé n'est pas un objet JSON.")
    return data


def _is_host_allowed(hostname: str, configured_base_url: str | None) -> bool:
    host = hostname.lower().strip()
    if not host:
        return False

    allowed_env = os.environ.get("IDHALL_ALLOWED_HOSTS", "").strip()
    if allowed_env:
        allowed_patterns = [p.strip().lower() for p in allowed_env.split(",") if p.strip()]
        for pat in allowed_patterns:
            if pat == "*":
                return True
            if pat.startswith("*.") and host.endswith(pat[1:]):
                return True
            if host == pat:
                return True
        return False

    if configured_base_url:
        cfg_host = (urlparse(configured_base_url).hostname or "").lower()
        if cfg_host and host == cfg_host:
            return True

    return host.endswith(DEFAULT_ALLOWED_SUFFIX)


def validate_base_url(url: str, configured_base_url: str | None = None) -> str:
    """Valide l'URL de base IDhall (HTTPS obligatoire + protection SSRF)."""
    cleaned = url.strip().rstrip("/")
    parsed = urlparse(cleaned)
    if parsed.scheme != "https" or not parsed.hostname:
        raise IDhallAuthError(
            f"URL de base IDhall invalide ({cleaned!r}) : une URL HTTPS valide est requise."
        )
    if not _is_host_allowed(parsed.hostname, configured_base_url):
        raise IDhallAuthError(
            f"Hôte IDhall non autorisé ({parsed.hostname!r}). "
            "Configurez IDHALL_BASE_URL ou IDHALL_ALLOWED_HOSTS si votre instance utilise un domaine personnalisé."
        )
    return cleaned


def resolve_credentials() -> IDhallCredentials:
    """Résout le jeton JWT de l'utilisateur courant.

    Priorité :
    1. En-tête HTTP ``Authorization: Bearer <jwt>`` (mode multi-utilisateurs HTTP/SSE).
    2. Variable d'environnement ``IDHALL_API_TOKEN`` (mode local stdio).
    """
    headers = get_http_headers(
        include={"authorization", "x-idhall-base-url", "accept-language", "idhall-timezone"}
    )
    # Normalise les clés d'en-têtes en minuscules
    norm_headers = {k.lower(): v for k, v in headers.items()}

    token: str | None = None
    auth_header = norm_headers.get("authorization", "").strip()
    if auth_header:
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
        else:
            token = auth_header

    if not token:
        token = os.environ.get("IDHALL_API_TOKEN", "").strip()

    if not token:
        raise IDhallAuthError(
            "Aucun jeton JWT IDhall fourni. "
            "En mode HTTP, passez votre jeton dans l'en-tête 'Authorization: Bearer <votre_jwt>'. "
            "En mode stdio local, définissez la variable d'environnement IDHALL_API_TOKEN."
        )

    claims = decode_jwt_payload(token)

    exp = claims.get("exp")
    if isinstance(exp, (int, float)) and exp < time.time():
        raise IDhallAuthError(
            "Votre jeton JWT IDhall est expiré. Générez un nouveau jeton dans "
            "IDhall (Mon compte > Connexion et sécurité > Jetons d'authentification pour l'API REST)."
        )

    configured_base = os.environ.get("IDHALL_BASE_URL", "").strip() or None
    header_base = norm_headers.get("x-idhall-base-url", "").strip() or None
    iss_base = claims.get("iss") if isinstance(claims.get("iss"), str) else None

    raw_base_url = header_base or configured_base or iss_base
    if not raw_base_url:
        raise IDhallAuthError(
            "Impossible de déterminer l'URL de base IDhall (ni en-tête X-IDhall-Base-Url, "
            "ni IDHALL_BASE_URL, ni claim JWT 'iss')."
        )

    base_url = validate_base_url(raw_base_url, configured_base_url=configured_base)
    language = norm_headers.get("accept-language") or os.environ.get("IDHALL_LANGUAGE", "fr")
    tz = norm_headers.get("idhall-timezone") or os.environ.get("IDHALL_TIMEZONE") or None

    return IDhallCredentials(
        token=token,
        base_url=base_url,
        language=language,
        timezone=tz,
        claims=claims,
    )
