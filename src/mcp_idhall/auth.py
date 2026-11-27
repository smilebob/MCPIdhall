"""Authentification JWT par utilisateur et résolution sécurisée (anti-SSRF) de l'URL IDhall."""

from __future__ import annotations

import base64
import ipaddress
import json
import os
import re
import socket
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

from fastmcp.server.dependencies import get_http_headers

DEFAULT_ALLOWED_SUFFIX = ".idhall.com"
MAX_JWT_BYTES = 8192
CLOCK_SKEW_SECONDS = 30
_SAFE_HEADER_RE = re.compile(r"^[A-Za-z0-9_./+\-,;= ]{1,64}$")

_ACTIVE_TRANSPORT: str = "stdio"


class IDhallAuthError(ValueError):
    """Erreur d'authentification ou de configuration de jeton JWT IDhall."""


def set_active_transport(transport: str) -> None:
    """Enregistre le transport actif ('stdio', 'streamable-http', 'sse') pour isoler le mode HTTP."""
    global _ACTIVE_TRANSPORT
    _ACTIVE_TRANSPORT = transport.strip().lower()


def get_active_transport() -> str:
    return _ACTIVE_TRANSPORT


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class IDhallCredentials:
    """Identifiants résolus pour l'appel courant (strictement isolés par requête)."""

    token: str = field(repr=False)
    base_url: str
    language: str = "fr"
    timezone: str | None = None
    claims: dict[str, Any] | None = None


def _sanitize_header_value(value: str | None, name: str, default: str | None = None) -> str | None:
    if value is None:
        return default
    cleaned = value.strip()
    if not cleaned:
        return default
    if "\r" in cleaned or "\n" in cleaned or "\x00" in cleaned or not _SAFE_HEADER_RE.match(cleaned):
        raise IDhallAuthError(f"Valeur d'en-tête invalide pour {name!r}.")
    return cleaned


def decode_jwt_payload(token: str) -> dict[str, Any]:
    """Décode la partie payload d'un JWT sans vérifier la signature (vérifiée côté IDhall)."""
    stripped = token.strip()
    if len(stripped) > MAX_JWT_BYTES:
        raise IDhallAuthError("Le jeton JWT dépasse la taille maximale autorisée.")
    if "\r" in stripped or "\n" in stripped or "\x00" in stripped:
        raise IDhallAuthError("Le jeton JWT contient des caractères de contrôle interdits.")

    parts = stripped.split(".")
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
    host = hostname.lower().strip().rstrip(".")
    if not host:
        return False

    allowed_env = os.environ.get("IDHALL_ALLOWED_HOSTS", "").strip()
    if allowed_env:
        allowed_patterns = [p.strip().lower().rstrip(".") for p in allowed_env.split(",") if p.strip()]
        for pat in allowed_patterns:
            if pat == "*":
                return True
            if pat.startswith("*.") and host.endswith(pat[1:]) and len(host) > len(pat[1:]):
                return True
            if host == pat:
                return True
        return False

    if configured_base_url:
        cfg_host = (urlparse(configured_base_url).hostname or "").lower().rstrip(".")
        if cfg_host and host == cfg_host:
            return True

    return host.endswith(DEFAULT_ALLOWED_SUFFIX) and len(host) > len(DEFAULT_ALLOWED_SUFFIX)


def _is_non_public_ip(ip_str: str) -> bool:
    ip = ipaddress.ip_address(ip_str)
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def _check_ssrf_network(hostname: str) -> None:
    """Bloque les adresses privées, loopback et metadata (anti-SSRF) sauf opt-in explicite."""
    if _env_flag("IDHALL_ALLOW_PRIVATE_NETWORKS", default=False):
        return

    host_lower = hostname.lower().rstrip(".")
    if host_lower in {"localhost", "ip6-localhost", "ip6-loopback"} or host_lower.endswith(".localhost"):
        raise IDhallAuthError(
            f"Hôte interne interdit ({hostname!r}) par la protection anti-SSRF. "
            "Définissez IDHALL_ALLOW_PRIVATE_NETWORKS=true uniquement pour une instance on-premise interne."
        )

    # Cas d'une adresse IP littérale
    try:
        if _is_non_public_ip(host_lower):
            raise IDhallAuthError(
                f"Adresse IP non publique interdite ({hostname!r}) par la protection anti-SSRF."
            )
        return
    except ValueError:
        pass

    # Résolution DNS si disponible (ne bloque pas si hors-ligne/tests mockés, mais bloque toute IP interne résolue)
    try:
        infos = socket.getaddrinfo(hostname, 443, type=socket.SOCK_STREAM)
    except OSError:
        return

    for info in infos:
        sockaddr = info[4]
        if not sockaddr:
            continue
        ip_str = str(sockaddr[0])
        if _is_non_public_ip(ip_str):
            raise IDhallAuthError(
                f"L'hôte {hostname!r} résout vers une adresse IP non publique ({ip_str}), "
                "bloquée par la protection anti-SSRF."
            )


def validate_base_url(url: str, configured_base_url: str | None = None) -> str:
    """Valide l'URL de base IDhall (HTTPS obligatoire, sans credentials/chemin, anti-SSRF)."""
    cleaned = url.strip().rstrip("/")
    parsed = urlparse(cleaned)
    if parsed.scheme != "https" or not parsed.hostname:
        raise IDhallAuthError(
            f"URL de base IDhall invalide ({cleaned!r}) : une URL HTTPS valide est requise."
        )
    if parsed.username or parsed.password:
        raise IDhallAuthError("L'URL de base IDhall ne doit pas contenir d'identifiants intégrés.")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise IDhallAuthError("L'URL de base IDhall ne doit contenir ni chemin, ni query, ni fragment.")
    if not _is_host_allowed(parsed.hostname, configured_base_url):
        raise IDhallAuthError(
            f"Hôte IDhall non autorisé ({parsed.hostname!r}). "
            "Configurez IDHALL_BASE_URL ou IDHALL_ALLOWED_HOSTS si votre instance utilise un domaine personnalisé."
        )
    _check_ssrf_network(parsed.hostname)
    return cleaned


def resolve_credentials() -> IDhallCredentials:
    """Résout le jeton JWT de l'utilisateur courant.

    Priorité :
    1. En-tête HTTP ``Authorization: Bearer <jwt>`` (obligatoire en mode HTTP multi-utilisateurs).
    2. Variable d'environnement ``IDHALL_API_TOKEN`` (uniquement en mode ``stdio``, ou si
       ``MCP_ALLOW_ENV_TOKEN_IN_HTTP=true`` est explicitement activé).
    """
    headers = get_http_headers(
        include={"authorization", "x-idhall-base-url", "accept-language", "idhall-timezone"}
    )
    norm_headers = {k.lower(): v for k, v in headers.items()}

    token: str | None = None
    auth_header = norm_headers.get("authorization", "").strip()
    if auth_header:
        if auth_header.lower().startswith("bearer "):
            token = auth_header[7:].strip()
        else:
            token = auth_header

    allow_env_fallback = _ACTIVE_TRANSPORT == "stdio" or _env_flag(
        "MCP_ALLOW_ENV_TOKEN_IN_HTTP", default=False
    )
    if not token and allow_env_fallback:
        token = os.environ.get("IDHALL_API_TOKEN", "").strip()

    if not token:
        raise IDhallAuthError(
            "Aucun jeton JWT IDhall fourni. "
            "En mode HTTP, passez votre jeton dans l'en-tête 'Authorization: Bearer <votre_jwt>'. "
            "En mode stdio local, définissez la variable d'environnement IDHALL_API_TOKEN."
        )

    claims = decode_jwt_payload(token)

    now = time.time()
    exp = claims.get("exp")
    if isinstance(exp, (int, float)) and exp < now - CLOCK_SKEW_SECONDS:
        raise IDhallAuthError(
            "Votre jeton JWT IDhall est expiré. Générez un nouveau jeton dans "
            "IDhall (Mon compte > Connexion et sécurité > Jetons d'authentification pour l'API REST)."
        )
    nbf = claims.get("nbf")
    if isinstance(nbf, (int, float)) and nbf > now + CLOCK_SKEW_SECONDS:
        raise IDhallAuthError("Votre jeton JWT IDhall n'est pas encore valide (claim 'nbf' dans le futur).")

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
    language = _sanitize_header_value(
        norm_headers.get("accept-language") or os.environ.get("IDHALL_LANGUAGE", "fr"),
        "Accept-Language",
        default="fr",
    ) or "fr"
    tz = _sanitize_header_value(
        norm_headers.get("idhall-timezone") or os.environ.get("IDHALL_TIMEZONE") or None,
        "IDhall-Timezone",
        default=None,
    )

    return IDhallCredentials(
        token=token,
        base_url=base_url,
        language=language,
        timezone=tz,
        claims=claims,
    )
