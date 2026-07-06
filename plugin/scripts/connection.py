#!/usr/bin/env python3
"""/skube connection helper — list the account's marketplace connections and pin ONE for the
session, PERSISTENTLY.

Skills call THIS instead of guessing/probing credential endpoints (which trips the
credential-scanning guard — and is exactly what a fresh, compacted session did). The only
endpoint used is the documented ``/v1/me/marketplaces``.

Usage:
  connection.py current   -> JSON {"pinned": <id|null>, "platform": ..., "market": ...}
  connection.py list      -> JSON {"pinned": <id|null>, "connections": [ {credential_id,
                             label, marketplace, connected}, ... ]}  (for the picker)
  connection.py pin <credential_id> [--platform amazon] [--market DE]
                          -> validate against the account's real connections, persist to
                             ~/.skube/.env, and echo to $CLAUDE_ENV_FILE so THIS session sees it.

Isolation: ``pin`` refuses any id the account does not actually own, so a product can never be
sent to a credential the seller has no claim to.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import bootstrap  # noqa: E402  (after sys.path tweak so it works regardless of cwd)


def _api() -> tuple[str, str]:
    bootstrap.load_dotenv()
    url = (os.environ.get("SKUBE_API_URL") or bootstrap.DEFAULT_API_URL).rstrip("/")
    key = os.environ.get("SKUBE_API_KEY", "")
    if not key.startswith("lk_live_"):
        raise SystemExit("SKUBE: not connected yet — run /skube:connect once.")
    return url, key


def list_connections() -> list[dict]:
    """Flatten /v1/me/marketplaces into one connection list (credential_id + label + marketplace)."""
    url, key = _api()
    req = urllib.request.Request(
        f"{url}/v1/me/marketplaces", headers={"Authorization": f"Bearer {key}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30, context=bootstrap._SSL_CTX) as resp:  # noqa: S310 (trusted Skube host)
            data = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"SKUBE: could not list your connections (HTTP {exc.code}).")
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"SKUBE: could not reach the Skube API: {exc}")
    out: list[dict] = []
    for mp in data.get("marketplaces", []):
        marketplace = str(mp.get("marketplace") or "").lower()
        for conn in mp.get("connections") or []:
            cid = conn.get("credential_id")
            if cid is None:
                continue
            out.append({
                "credential_id": str(cid),
                "label": conn.get("label") or "",
                "marketplace": marketplace,
                "connected": bool(mp.get("connected")),
            })
    return out


def cmd_current() -> int:
    bootstrap.load_dotenv()
    cid = (os.environ.get("SKUBE_CREDENTIAL_ID") or "").strip()
    print(json.dumps({
        "pinned": cid or None,
        "platform": (os.environ.get("SKUBE_PLATFORM") or "").strip(),
        "market": (os.environ.get("SKUBE_MARKETPLACE") or "").strip(),
    }))
    return 0


def cmd_list() -> int:
    conns = list_connections()
    bootstrap.load_dotenv()
    print(json.dumps({
        "pinned": (os.environ.get("SKUBE_CREDENTIAL_ID") or "").strip() or None,
        "connections": conns,
    }, ensure_ascii=False))
    return 0


def cmd_pin(credential_id: str, platform: str | None, market: str | None) -> int:
    conns = list_connections()
    match = next((c for c in conns if c["credential_id"] == credential_id.strip()), None)
    if match is None:
        raise SystemExit(
            f"SKUBE: {credential_id} is not one of your connections — run `connection.py list` and "
            "pick one of those ids."
        )
    dest = bootstrap.save_credential_id(
        credential_id, platform or match["marketplace"], market or "DE"
    )
    # Make THIS session see it immediately (bootstrap-style append to the harness env file).
    env_file = os.environ.get("CLAUDE_ENV_FILE", "").strip()
    if env_file:
        try:
            with open(env_file, "a", encoding="utf-8") as fh:
                fh.write(f"export SKUBE_CREDENTIAL_ID={credential_id.strip()}\n")
        except Exception:  # noqa: BLE001 — never break over env-file plumbing
            pass
    print(f"SKUBE: pinned connection {match['label'] or credential_id} "
          f"({match['marketplace']}) → saved to {dest}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Skube connection picker")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("current")
    sub.add_parser("list")
    pin = sub.add_parser("pin")
    pin.add_argument("credential_id")
    pin.add_argument("--platform")
    pin.add_argument("--market")
    args = parser.parse_args()
    if args.cmd == "current":
        return cmd_current()
    if args.cmd == "list":
        return cmd_list()
    if args.cmd == "pin":
        return cmd_pin(args.credential_id, args.platform, args.market)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
