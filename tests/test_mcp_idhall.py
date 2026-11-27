"""Tests unitaires et de sécurité pour MCPIdhall (auth, anti-SSRF, path traversal, read-only, FastMCP)."""

from __future__ import annotations

import base64
import json
import time
from typing import Any
from unittest.mock import patch

import httpx
import pytest
import respx

from mcp_idhall.auth import (
    IDhallAuthError,
    IDhallCredentials,
    resolve_credentials,
    set_active_transport,
    validate_base_url,
)
from mcp_idhall.catalog import get_endpoint_spec, search_endpoints
from mcp_idhall.client import IDhallAPIError, IDhallClient, normalize_api_path
from mcp_idhall.server import idhall_get_endpoint_spec, mcp


def _make_fake_jwt(payload: dict[str, Any]) -> str:
    header = (
        base64.urlsafe_b64encode(json.dumps({"typ": "JWT", "alg": "RS256"}).encode())
        .rstrip(b"=")
        .decode()
    )
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    return f"{header}.{body}.fakesig"


@pytest.fixture(autouse=True)
def _reset_transport() -> Any:
    set_active_transport("stdio")
    yield
    set_active_transport("stdio")


# ---------------------------------------------------------------------------
# Auth, isolation multi-utilisateurs & anti-SSRF
# ---------------------------------------------------------------------------


def test_resolve_credentials_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("IDHALL_API_TOKEN", raising=False)
    monkeypatch.delenv("IDHALL_BASE_URL", raising=False)
    with patch("mcp_idhall.auth.get_http_headers", return_value={}):
        with pytest.raises(IDhallAuthError, match="Aucun jeton JWT"):
            resolve_credentials()


def test_resolve_credentials_http_mode_blocks_env_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    set_active_transport("streamable-http")
    env_tok = _make_fake_jwt({"iss": "https://env.idhall.com", "sub": 1, "exp": int(time.time()) + 3600})
    monkeypatch.setenv("IDHALL_API_TOKEN", env_tok)
    monkeypatch.delenv("MCP_ALLOW_ENV_TOKEN_IN_HTTP", raising=False)
    with patch("mcp_idhall.auth.get_http_headers", return_value={}):
        with pytest.raises(IDhallAuthError, match="Aucun jeton JWT"):
            resolve_credentials()


def test_resolve_credentials_expired_and_nbf_token(monkeypatch: pytest.MonkeyPatch) -> None:
    expired = _make_fake_jwt({"iss": "https://demo.idhall.com", "sub": 1, "exp": int(time.time()) - 120})
    monkeypatch.setenv("IDHALL_API_TOKEN", expired)
    with patch("mcp_idhall.auth.get_http_headers", return_value={}):
        with pytest.raises(IDhallAuthError, match="expiré"):
            resolve_credentials()

    future_nbf = _make_fake_jwt({"iss": "https://demo.idhall.com", "sub": 1, "nbf": int(time.time()) + 300})
    monkeypatch.setenv("IDHALL_API_TOKEN", future_nbf)
    with patch("mcp_idhall.auth.get_http_headers", return_value={}):
        with pytest.raises(IDhallAuthError, match="nbf"):
            resolve_credentials()


def test_resolve_credentials_http_header_overrides_env(monkeypatch: pytest.MonkeyPatch) -> None:
    env_tok = _make_fake_jwt({"iss": "https://env.idhall.com", "sub": 1, "exp": int(time.time()) + 3600})
    user_tok = _make_fake_jwt({"iss": "https://user.idhall.com", "sub": 99, "exp": int(time.time()) + 3600})
    monkeypatch.setenv("IDHALL_API_TOKEN", env_tok)
    monkeypatch.delenv("IDHALL_BASE_URL", raising=False)

    with patch(
        "mcp_idhall.auth.get_http_headers",
        return_value={"authorization": f"Bearer {user_tok}", "accept-language": "en"},
    ):
        creds = resolve_credentials()

    assert creds.token == user_tok
    assert creds.base_url == "https://user.idhall.com"
    assert creds.claims is not None and creds.claims["sub"] == 99
    assert creds.language == "en"
    assert user_tok not in repr(creds)


def test_resolve_credentials_rejects_header_injection(monkeypatch: pytest.MonkeyPatch) -> None:
    tok = _make_fake_jwt({"iss": "https://user.idhall.com", "sub": 1, "exp": int(time.time()) + 3600})
    with patch(
        "mcp_idhall.auth.get_http_headers",
        return_value={"authorization": f"Bearer {tok}", "accept-language": "fr\r\nX-Injected: yes"},
    ):
        with pytest.raises(IDhallAuthError, match="en-tête invalide"):
            resolve_credentials()


def test_validate_base_url_blocks_ssrf(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("IDHALL_ALLOWED_HOSTS", raising=False)
    monkeypatch.delenv("IDHALL_ALLOW_PRIVATE_NETWORKS", raising=False)

    with pytest.raises(IDhallAuthError, match="HTTPS"):
        validate_base_url("http://example.idhall.com")
    with pytest.raises(IDhallAuthError, match="identifiants"):
        validate_base_url("https://user:pass@example.idhall.com")
    with pytest.raises(IDhallAuthError, match="chemin"):
        validate_base_url("https://example.idhall.com/evil")
    with pytest.raises(IDhallAuthError, match="non autorisé"):
        validate_base_url("https://evil.example.com")

    # Même avec IDHALL_ALLOWED_HOSTS=*, les IP privées / metadata / localhost restent bloquées
    monkeypatch.setenv("IDHALL_ALLOWED_HOSTS", "*")
    for internal in (
        "https://localhost",
        "https://127.0.0.1",
        "https://169.254.169.254",
        "https://10.0.0.5",
        "https://192.168.1.10",
    ):
        with pytest.raises(IDhallAuthError, match="anti-SSRF"):
            validate_base_url(internal)

    # DNS qui résout vers une IP privée doit aussi être bloqué
    with patch("mcp_idhall.auth.socket.getaddrinfo", return_value=[(2, 1, 6, "", ("10.0.0.42", 443))]):
        with pytest.raises(IDhallAuthError, match="non publique"):
            validate_base_url("https://internal.idhall.com")

    # Opt-in explicite pour une instance on-premise interne
    monkeypatch.setenv("IDHALL_ALLOW_PRIVATE_NETWORKS", "true")
    assert validate_base_url("https://10.0.0.5") == "https://10.0.0.5"


# ---------------------------------------------------------------------------
# Client HTTP, Anti-Path-Traversal, Read-Only & Rate Limit
# ---------------------------------------------------------------------------


def test_normalize_api_path() -> None:
    assert normalize_api_path("ideas") == "/api/v1/ideas"
    assert normalize_api_path("/ideas/42") == "/api/v1/ideas/42"
    assert normalize_api_path("/api/ideas") == "/api/v1/ideas"
    assert normalize_api_path("/api/v1/ideas") == "/api/v1/ideas"

    for bad in (
        "https://example.idhall.com/api/v1/ideas",
        "//evil.com/steal",
        "/api/v1/ideas/../../admin",
        "/api/v1/ideas/%2e%2e/admin",
        "/api/v1/ideas?foo=bar",
        "/api/v1/ideas#frag",
        "/api/v1/ideas\r\nX-Test: 1",
    ):
        with pytest.raises(ValueError):
            normalize_api_path(bad)


@respx.mock
async def test_client_props_and_filter_and_retry_429() -> None:
    tok = _make_fake_jwt({"iss": "https://example.idhall.com", "sub": 53, "exp": int(time.time()) + 3600})
    creds = IDhallCredentials(token=tok, base_url="https://example.idhall.com")
    client = IDhallClient(creds, max_retries=3)

    route = respx.get("https://example.idhall.com/api/v1/ideas").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}),
            httpx.Response(200, json={"records": [{"id": 1, "title": "Test"}], "offset": 0, "page_size": 20}),
        ]
    )

    res = await client.request(
        "GET",
        "/api/v1/ideas",
        query_params={"props": ["title", "plan"], "filter": {"plan": 27}, "count": True},
    )
    assert res["records"][0]["id"] == 1
    assert route.call_count == 2
    sent = route.calls[1].request
    assert not sent.url.params
    assert json.loads(sent.content.decode()) == {
        "props": ["title", "plan"],
        "filter": {"plan": 27},
        "count": True,
    }


async def test_client_read_only_mode_blocks_writes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("IDHALL_READ_ONLY", "true")
    tok = _make_fake_jwt({"iss": "https://example.idhall.com", "sub": 53, "exp": int(time.time()) + 3600})
    creds = IDhallCredentials(token=tok, base_url="https://example.idhall.com")
    client = IDhallClient(creds)

    with pytest.raises(IDhallAPIError) as exc_info:
        await client.request("DELETE", "/api/v1/ideas/1")
    assert exc_info.value.status_code == 403
    assert "lecture seule" in str(exc_info.value)


@respx.mock
async def test_client_formats_problem_details_error() -> None:
    tok = _make_fake_jwt({"iss": "https://example.idhall.com", "sub": 53, "exp": int(time.time()) + 3600})
    creds = IDhallCredentials(token=tok, base_url="https://example.idhall.com")
    client = IDhallClient(creds)

    respx.get("https://example.idhall.com/api/v1/ideas/999999").mock(
        return_value=httpx.Response(
            404,
            headers={"Content-Type": "application/problem+json"},
            json={"title": "Élément introuvable", "issue_code": 12, "status": 404},
        )
    )

    with pytest.raises(IDhallAPIError) as exc_info:
        await client.request("GET", "/api/v1/ideas/999999")
    assert exc_info.value.status_code == 404
    assert "Élément introuvable" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Catalogue local, validation endpoint_id & annotations FastMCP
# ---------------------------------------------------------------------------


def test_local_catalog_search_and_spec() -> None:
    hits = search_endpoints(query="action-plan tasks", method="POST")
    assert any(h["endpoint_id"] == "POST__ideas__(id)__action-plan__tasks" for h in hits)
    spec = get_endpoint_spec("POST__ideas")
    assert spec is not None
    assert spec["method"] == "POST"


async def test_get_endpoint_spec_blocks_traversal() -> None:
    with pytest.raises(ValueError, match="Identifiant d'endpoint invalide"):
        await idhall_get_endpoint_spec("../../etc/passwd")


async def test_fastmcp_tools_registered_with_annotations() -> None:
    tools = await mcp.list_tools()
    by_name = {t.name: t for t in tools}
    assert len(by_name) == 33
    assert by_name["idhall_list_ideas"].annotations is not None
    assert by_name["idhall_list_ideas"].annotations.read_only_hint is True
    assert by_name["idhall_delete_idea"].annotations is not None
    assert by_name["idhall_delete_idea"].annotations.destructive_hint is True
    assert by_name["idhall_api_request"].annotations is not None
    assert by_name["idhall_api_request"].annotations.destructive_hint is True
