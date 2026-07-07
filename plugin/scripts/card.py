#!/usr/bin/env python3
"""Deterministic Skube job-card renderer — the plugin twin of the engine's render_card.py.

Job skills (status / diagnose / update / sales) build ONLY the data structure ``D``
(schema: ../CARD_DESIGN.md) and run this script; it prints a **Markdown** card — plain
GFM, NO widget/HTML. A ``show_widget`` render costs a ``read_me`` + ``show_widget``
round-trip and leaves a large HTML blob in context for the whole session; Markdown is
instant and weightless. ``to_markdown`` is kept BYTE-IDENTICAL to
``served-engine/core/render_card.py::to_markdown`` (one look, zero drift — a test in
``api/tests/test_card.py`` asserts both render the same output).

    python3 card.py <d.json>          # or:  echo '{...}' | python3 card.py -
"""

from __future__ import annotations

import json
import pathlib
import sys

_STATUS_FALLBACK = {"ask": "⏸️ needs your answer", "done": "✅ done"}


def _cell(v) -> str:
    """One GFM table cell: pipes/newlines escaped so a value can never break the table."""
    if v is None:
        return ""
    return str(v).replace("|", "\\|").replace("\n", " ").strip()


def _table(cols: list, rows: list) -> str:
    n = len(cols)
    head = "| " + " | ".join(_cell(c) for c in cols) + " |"
    sep = "| " + " | ".join("---" for _ in cols) + " |"
    body = ["| " + " | ".join(_cell(c) for c in (list(r) + [""] * n)[:n]) + " |" for r in rows]
    return "\n".join([head, sep, *body])


def to_markdown(data: dict) -> str:
    """Render card data (head + chips + sections) as a GFM Markdown card.

    Kept IDENTICAL to served-engine/core/render_card.py::to_markdown (one look, zero drift).
    ``sections`` items: ``table`` (GFM, all rows), ``tree`` (fenced ```text), ``buttons``
    (a "To clarify" question, recommended option bold). A ``fold`` table is the raw input
    echo — collapsed to a one-line hint.
    """
    tr = data.get("_t") or {}
    head = data.get("head") or {}
    emoji = head.get("emoji", "")
    title = head.get("title", "skube")
    status = tr.get(head.get("status")) or _STATUS_FALLBACK.get(head.get("status"), "")
    step = head.get("step")
    # checkpoint cards carry step ("1/7"); job cards (status/diagnose/…) carry job ("Sales").
    prefix = f"{tr.get('step', 'Step')} {step}" if step else (head.get("job") or "")
    lead = f"{emoji} " if emoji else ""
    header = f"## {lead}{prefix} · {title}" if prefix else f"## {lead}{title}"
    if status:
        header += f" — {status}"
    parts: list[str] = [header]

    chips = [c for c in (data.get("chips") or []) if c.get("l")]
    if chips:
        parts += ["", " · ".join(f"**{c.get('v')}** {c.get('l')}" for c in chips)]

    sections = data.get("sections") or []
    for s in (x for x in sections if x.get("t") in ("table", "tree")):
        title_s = s.get("title")
        if s.get("t") == "table":
            if s.get("fold"):  # raw input echo → hint, not the whole dump
                parts += ["", f'_{title_s}_ — say **“columns”** to list them all.']
                continue
            parts += (["", f"### {title_s}"] if title_s else [""])
            parts.append(_table(s.get("cols") or [], s.get("rows") or []))
        else:  # tree
            parts += (["", f"### {title_s}"] if title_s else [""])
            parts.append("```text\n" + str(s.get("text", "")).rstrip() + "\n```")

    buttons = [s for s in sections if s.get("t") == "buttons"]
    if buttons:
        parts += ["", "**To clarify:**"]
        for i, b in enumerate(buttons, 1):
            opts = [f"**{o.get('label', '')} (recommended)**" if o.get("primary")
                    else o.get("label", "") for o in (b.get("items") or [])]
            note = f" ({b['note']})" if b.get("note") else ""
            parts.append(f"{i}. **{b.get('title', '')}**{note} — " + " / ".join(opts))
        parts += ["", '**Next:** "ok" = continue · reply with a number to pick an option']
    else:
        parts += ["", '**Next:** "ok" = continue']

    return "\n".join(parts).strip() + "\n"


def main() -> None:
    src = sys.argv[1] if len(sys.argv) > 1 else "-"
    raw = sys.stdin.read() if src == "-" else pathlib.Path(src).read_text(encoding="utf-8")
    d = json.loads(raw)
    head = d.get("head") if isinstance(d, dict) else None
    if not isinstance(head, dict) or "title" not in head:
        raise SystemExit('D braucht mindestens {"head": {"title": …, "status": "done|ask", '
                         '"job" oder "step": …}} — Schema: CARD_DESIGN.md')
    print(to_markdown(d), end="")


if __name__ == "__main__":
    main()
