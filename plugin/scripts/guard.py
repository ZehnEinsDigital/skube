#!/usr/bin/env python3
"""Skube plugin PreToolUse guard (defense-in-depth, NOT the security boundary).

The real safety boundary is server-side: Amazon credentials and the live SP-API write
live only in the Skube cloud, so the client physically cannot perform a live write.
This guard is belt-and-suspenders for the customer's own machine: it denies
- any command that talks directly to Amazon SP-API (sellingpartnerapi egress),
- python invocations that would skip the safety shim (-S/-E/-I).

NOTE: it does NOT block writes under SKUBE_ENGINE_DIR — that points at the customer's
own writable engine working copy, which the engine MUST write to (seeded brain/cache +
run output). The engine source is not a client-side secret; the moat is the gated cloud
(credentials, uploads, fresh brain), not a read-only lock on the user's own files.

Reads the PreToolUse JSON on stdin and prints a deny decision (or nothing = allow).
Must never crash the tool call.
"""

import json
import re
import sys

_SP_API = "sellingpartnerapi"
_PY_SKIP = re.compile(r"(?<![\w-])python[0-9.]*\s+(?:-[A-Za-z]*[SEI][A-Za-z]*\b)")


def _deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))


def evaluate(tool_name: str, tool_input: dict) -> str | None:
    blob = json.dumps(tool_input or {}).lower()
    if _SP_API in blob:
        return ("Direct Amazon SP-API access is not allowed from the plugin. Listing reads "
                "and writes go through the Skube cloud gateway (your credentials never leave it).")
    if tool_name == "Bash":
        cmd = str((tool_input or {}).get("command", ""))
        if _PY_SKIP.search(cmd):
            return "python with -S/-E/-I would skip the Skube safety shim."
    return None


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except Exception:
        return  # fail-open: this is defense-in-depth, the server is the real boundary
    reason = evaluate(data.get("tool_name", ""), data.get("tool_input", {}) or {})
    if reason:
        _deny(reason)


if __name__ == "__main__":
    main()
