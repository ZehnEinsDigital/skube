#!/usr/bin/env python3
"""Deterministic Skube job-card renderer — the plugin twin of the engine's render_card.py.

Job skills (status / diagnose / update / sales) build ONLY the data structure ``D``
(schema: ../CARD_DESIGN.md), write it to a JSON file, and run this script; the layout
comes from the canonical card JS, which ``build-plugin-release.sh`` mirrors from
``served-engine/core/render_card.py`` into CARD_DESIGN.md at every release. This script
reads the JS from there at runtime — one look, zero drift, no hand-written HTML.

    python3 card.py <d.json>          # or:  echo '{...}' | python3 card.py -
"""

from __future__ import annotations

import json
import pathlib
import re
import sys


def _js() -> str:
    md = (pathlib.Path(__file__).resolve().parent.parent / "CARD_DESIGN.md").read_text(
        encoding="utf-8"
    )
    m = re.search(r"<script>\nconst D=\{[^\n]*\n(.*?)\n</script>", md, re.S)
    if not m:
        raise SystemExit("CARD_DESIGN.md: Standard-JS-Block nicht gefunden — Plugin beschädigt?")
    return m.group(1).rstrip()


def main() -> None:
    src = sys.argv[1] if len(sys.argv) > 1 else "-"
    raw = sys.stdin.read() if src == "-" else pathlib.Path(src).read_text(encoding="utf-8")
    d = json.loads(raw)
    head = d.get("head") if isinstance(d, dict) else None
    if not isinstance(head, dict) or "title" not in head:
        raise SystemExit('D braucht mindestens {"head": {"title": …, "status": "done|ask", '
                         '"job" oder "step": …}} — Schema: CARD_DESIGN.md')
    payload = json.dumps(d, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    print(
        '<div id="sk-card" style="padding:0.5rem 0"></div>\n'
        f"<script>\nconst D={payload};\n{_js()}\n</script>"
    )


if __name__ == "__main__":
    main()
