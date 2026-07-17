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
import connection  # noqa: E402  (same scripts dir)


def main() -> None:
    bootstrap.load_dotenv()  # pick up SKUBE_API_URL from ~/.skube/.env (GUI has no shell env)
    api_url = (os.environ.get("SKUBE_API_URL") or bootstrap.DEFAULT_API_URL).strip()
    if len(sys.argv) > 1 and sys.argv[1] == "wait":
        # Phase 2 (cloud/headless): poll for the approval parked by a previous run. Bounded —
        # prints SKUBE-PENDING and exits cleanly while not yet approved; the trigger re-runs it.
        dest = bootstrap.device_wait()
        if dest is None:
            return
    else:
        opened = bootstrap.device_start(api_url)
        if not opened:
            # No local browser (cloud/headless): exit NOW so the link above actually renders —
            # polling in-process would hide it behind a spinner until the code expires.
            print(
                "SKUBE-PENDING: waiting for approval. After the user clicked Authorize, run "
                "this script again with the argument: wait"
            )
            return
        dest = bootstrap.device_wait(max_wait=600)  # desktop: browser is open, finish in one go
        if dest is None:
            raise SystemExit("SKUBE: authorization timed out. Run /skube:connect again.")
    # Auto-pin when the account has exactly ONE connection, so a single-seller never has to
    # re-pick "which account?" in a later (or compacted) session. Several (agency) → leave
    # unpinned; the skill asks which, then pins. Best-effort: never fail connect over this.
    note = ""
    try:
        conns = connection.list_connections()
        if len(conns) == 1:
            only = conns[0]
            bootstrap.save_credential_id(only["credential_id"], only["marketplace"], "DE")
            note = f" Account: {only['label'] or only['marketplace']} (pinned)."
        elif len(conns) > 1:
            note = f" You have {len(conns)} connections — I'll ask which one at list/upload time."
    except SystemExit:
        pass  # listing failed (e.g. transient) — connect still succeeded; skill will pin later
    print(f"SKUBE connected: saved to {dest}.{note} Just describe what you want to list on Amazon.")


if __name__ == "__main__":
    main()
