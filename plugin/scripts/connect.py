#!/usr/bin/env python3
"""/skube:connect helper — connect this device to a Skube account via the browser.

Opens the browser device-auth flow (like `gh login`): the user clicks Authorize and the key is
delivered + saved to ~/.skube/.env automatically. No key paste, no file editing.

SKUBE_API_URL selects the cloud (defaults to the hosted cloud). It's read from the environment OR
from ~/.skube/.env — so a GUI user with no shell env can point at a local stack by putting a single
line `SKUBE_API_URL=http://localhost:8000` in ~/.skube/.env first.

Advanced/CI (no browser): write `SKUBE_API_KEY=lk_live_…` into ~/.skube/.env directly instead.
"""

from __future__ import annotations

import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import bootstrap  # noqa: E402  (after sys.path tweak so it works regardless of cwd)


def main() -> None:
    bootstrap.load_dotenv()  # pick up SKUBE_API_URL from ~/.skube/.env (GUI has no shell env)
    api_url = (os.environ.get("SKUBE_API_URL") or bootstrap.DEFAULT_API_URL).strip()
    dest = bootstrap.connect_via_browser(api_url)
    print(f"SKUBE connected: saved to {dest}. Just describe what you want to list on Amazon.")


if __name__ == "__main__":
    main()
