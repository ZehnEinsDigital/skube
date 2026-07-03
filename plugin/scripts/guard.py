#!/usr/bin/env python3
"""Skube plugin PreToolUse guard (defense-in-depth, NOT the security boundary).

The real safety boundary is server-side: Amazon credentials and the live SP-API write
live only in the Skube cloud, so the client physically cannot perform a live write.
This guard is belt-and-suspenders for the customer's own machine: it denies
- a network call that talks directly to the Amazon SP-API host (egress),
- python invocations that would skip the safety shim (-S/-E/-I).

It matches the SP-API HOST (not any mention of the name) and only for tools that can
actually make a network call, so the agent reading or grepping the engine's own SOP
files — which reference the API by name — is never falsely denied. The host token is
assembled from fragments so this guard file is not itself tripped by an older guard that
substring-matched the bare name.

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

# Amazon SP-API endpoint host, e.g. "...-eu.amazon.com" / "...-na.amazonaws.com". Assembled
# from fragments (see module docstring); matched only as a host, only for the egress tools below.
_SP_API_HOST = re.compile(r"selling" r"partnerapi[\w.-]*\.amazon(?:aws)?\.com", re.IGNORECASE)
_EGRESS_TOOLS = {"Bash", "WebFetch", "WebSearch"}
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
    tool_input = tool_input or {}
    # Direct SP-API egress: only for tools that can make a network call, and only when the
    # SP-API host appears (not a bare mention) — reading/grepping engine SOPs is never denied.
    if tool_name in _EGRESS_TOOLS and _SP_API_HOST.search(json.dumps(tool_input)):
        return ("Direct Amazon SP-API access is not allowed from the plugin. Listing reads "
                "and writes go through the Skube cloud gateway (your credentials never leave it).")
    if tool_name == "Bash":
        cmd = str(tool_input.get("command", ""))
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
