"""Tests unitaires pour MCPIdhall (auth par utilisateur, client HTTP, catalogue, FastMCP)."""

from __future__ import annotations

import base64
import json
import time
from unittest.mock import patch

import httpx
import pytest
import respx

from mcp_idhall.auth import (
    IDhallAuthError,
    IDhallCredentials,
    decode_jwt_payload,
    resolve_credentials,
    validate_base_url,
)
from mcp_idhall.catalog import get_endpoint_spec, search_endpoints
from mcp_idhall.client import IDhallAPIError, IDhallClient, normalize_api_path
from mcp_idhall.server import mcp


def _make_fake_jwt(payload: dict) -> str:
    header = base64.urlsafe_b64encode(json.dumps({"typ": "JWT", "alg": "RS256"}).encode()).rstrip(b"=").decode()
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    return f"{header}.{body}.fakesig"


# ---------------------------------------------------------------------------
# Auth & isolation par utilisateur
# ---------------------------------------------------------------------------


def test_resolve_credentials_missing_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("IDHALL_API_TOKEN", raising=False)
    monkeypatch.delenv("IDHALL_BASE_URL", raising=False)
    with patch("mcp_idhall.auth.get_http_headers", return_value={}):
        with pytest.raises(IDhallAuthError, match="Aucun jeton JWT"):
            resolve_credentials()


def test_resolve_credentials_expired_token(monkeypatch: pytest.MonkeyPatch) -> None:
    expired = _make_fake_jwt({"iss": "https://demo.idhall.com", "sub": 1, "exp": int(time.time()) - 10})
    monkeypatch.setenv("IDHALL_API_TOKEN", expired)
    with patch("mcp_idhall.auth.get_http_headers", return_value={}):
        with pytest.raises(IDhallAuthError, match="expiré"):
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


def test_validate_base_url_blocks_ssrf(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("IDHALL_ALLOWED_HOSTS", raising=False)
    with pytest.raises(IDhallAuthError, match="HTTPS"):
        validate_base_url("http://example.idhall.com")
    with pytest.raises(IDhallAuthError, match="non autorisé"):
        validate_base_url("https://evil.example.com")
    assert validate_base_url("https://example.idhall.com/") == "https://example.idhall.com"


# ---------------------------------------------------------------------------
# Client HTTP & Rate Limit
# ---------------------------------------------------------------------------


def test_normalize_api_path() -> None:
    assert normalize_api_path("ideas") == "/api/v1/ideas"
    assert normalize_api_path("/ideas/42") == "/api/v1/ideas/42"
    assert normalize_api_path("/api/ideas") == "/api/v1/ideas"
    assert normalize_api_path("/api/v1/ideas") == "/api/v1/ideas"
    with pytest.raises(ValueError):
        normalize_api_path("https://example.idhall.com/api/v1/ideas")


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
# Catalogue local & enregistrement des outils FastMCP
# ---------------------------------------------------------------------------


def test_local_catalog_search_and_spec() -> None:
    hits = search_endpoints(query="action-plan tasks", method="POST")
    assert any(h["endpoint_id"] == "POST__ideas__(id)__action-plan__tasks" for h in hits)
    spec = get_endpoint_spec("POST__ideas")
    assert spec is not None
    assert spec["method"] == "POST"


async def test_fastmcp_tools_registered() -> None:
    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    assert "idhall_whoami" in names
    assert "idhall_list_ideas" in names
    assert "idhall_create_idea" in names
    assert "idhall_transition_idea_stage" in names
    assert "idhall_api_request" in names
    assert len(names) >= 30
