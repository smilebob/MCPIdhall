#!/usr/bin/env python3
"""Fetch the complete IDhall REST API v1 self-documentation into docs/idhall_api_reference.json.

Respects rate limits with polite pacing and exponential backoff on HTTP 429,
and supports resuming from an existing partial export.
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"
OUT_PATH = ROOT / "docs" / "idhall_api_reference.json"


def load_env(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    if not path.exists():
        raise FileNotFoundError(f"Missing {path}")
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def fetch_json(url: str, headers: dict[str, str], max_retries: int = 6) -> object:
    delay = 3.0
    for attempt in range(1, max_retries + 1):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                retry_after = e.headers.get("Retry-After")
                wait_s = float(retry_after) if retry_after and retry_after.isdigit() else delay
                print(
                    f"[429] Rate limited on {url} (attempt {attempt}/{max_retries}), sleeping {wait_s:.1f}s...",
                    file=sys.stderr,
                    flush=True,
                )
                time.sleep(wait_s)
                delay = min(delay * 2.0, 60.0)
                continue
            body = e.read(300).decode("utf-8", "replace")
            raise RuntimeError(f"HTTP {e.code} on {url}: {body}") from e
        except urllib.error.URLError as e:
            if attempt < max_retries:
                print(
                    f"[NET] Error on {url}: {e} (attempt {attempt}/{max_retries}), sleeping {delay:.1f}s...",
                    file=sys.stderr,
                    flush=True,
                )
                time.sleep(delay)
                delay = min(delay * 2.0, 60.0)
                continue
            raise
    raise RuntimeError(f"Failed after {max_retries} retries: {url}")


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def main() -> None:
    env = load_env(ENV_PATH)
    base_url = env["IDHALL_BASE_URL"].rstrip("/")
    token = env["IDHALL_API_TOKEN"]
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
        "Accept-Language": "fr",
    }

    existing_details: dict[str, dict] = {}
    if OUT_PATH.exists():
        try:
            prev = json.loads(OUT_PATH.read_text(encoding="utf-8"))
            existing_details = prev.get("endpoint_details", {})
            print(f"Resuming with {len(existing_details)} cached endpoints.", flush=True)
        except Exception:
            pass

    print("Fetching /api/v1/about ...", flush=True)
    about = fetch_json(f"{base_url}/api/v1/about", headers)
    time.sleep(0.35)

    print("Fetching /api/v1/reference/endpoints ...", flush=True)
    endpoints_index = fetch_json(f"{base_url}/api/v1/reference/endpoints", headers)
    if not isinstance(endpoints_index, list):
        raise RuntimeError(f"Expected list from reference/endpoints, got {type(endpoints_index)}")

    total = len(endpoints_index)
    print(f"Found {total} endpoints.", flush=True)

    details: dict[str, dict] = dict(existing_details)
    fetched_new = 0

    for idx, entry in enumerate(endpoints_index, 1):
        link = entry["link"]
        ep_id = link.rsplit("/", 1)[-1]
        if ep_id in details:
            continue

        detail = fetch_json(link, headers)
        details[ep_id] = detail
        fetched_new += 1

        if idx % 20 == 0 or idx == total:
            print(f"Progress: {len(details)}/{total} ({fetched_new} newly fetched)", flush=True)
            save_json(
                OUT_PATH,
                {
                    "exported_at": datetime.now(timezone.utc).isoformat(),
                    "base_url": base_url,
                    "about": about,
                    "endpoints_count": total,
                    "endpoints_index": endpoints_index,
                    "endpoint_details": details,
                },
            )
        time.sleep(0.35)

    save_json(
        OUT_PATH,
        {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "base_url": base_url,
            "about": about,
            "endpoints_count": total,
            "endpoints_index": endpoints_index,
            "endpoint_details": details,
        },
    )
    print(f"Done! Saved {len(details)}/{total} endpoints to {OUT_PATH}", flush=True)


if __name__ == "__main__":
    main()
