#!/usr/bin/env python3
"""Persist a connector-minted session key — the /skube:connect connector branch (E2.0-B4).

Reads the key from STDIN (never argv — nothing lands in process lists or shell history), saves it
via bootstrap.save_api_key (~/.skube/.env, chmod 600, merge-not-clobber) and exports it into
$CLAUDE_ENV_FILE so THIS session sees it immediately. Prints a one-line confirmation only — the
key itself is never echoed.
"""

from __future__ import annotations

import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import bootstrap  # noqa: E402


def main() -> None:
    key = sys.stdin.read().strip()
    dest = bootstrap.save_api_key(
        key, os.environ.get("SKUBE_API_URL") or bootstrap.DEFAULT_API_URL
    )
    env_file = os.environ.get("CLAUDE_ENV_FILE", "").strip()
    if env_file:
        try:
            with open(env_file, "a", encoding="utf-8") as fh:
                fh.write(f"export SKUBE_API_KEY={key}\n")
        except Exception:  # noqa: BLE001 — never break connect over env-file plumbing
            pass
    print(f"SKUBE connected via your Claude account: saved to {dest}.")


if __name__ == "__main__":
    main()
