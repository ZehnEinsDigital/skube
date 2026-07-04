---
name: diagnose
description: Find out why an Amazon SKU/listing was rejected, suppressed, errored, or isn't showing — and fix it. Use whenever the user asks why a listing failed/is suppressed/has errors/isn't live and wants it sorted.
when_to_use: 'Trigger on: "warum wurde X abgelehnt", "warum ist mein Listing unterdrückt", "SKU Y wird nicht angezeigt", "warum hat Amazon das geblockt", "fix my rejected listing", "why was my SKU rejected".'
---

Help the user fix an Amazon problem, in plain language, right here in this chat. Hide technical detail
(no "gateway", "bootstrap", paths). Answer in the user's language. Never tell them to open a folder.

**Stay in Skube's lane — ask before touching anything that isn't Skube.** You may have OTHER tools or MCP
servers connected in this session (Baselinker, other marketplaces, databases, files) — those are the user's
OWN connections, NOT part of Skube. Do this with **Skube's own gateway/commands only**. If you're missing
something another connected service could supply (e.g. a SKU/EAN you don't have), **stop and ASK the user
first** — name the service and exactly what you'd pull — and use it only after a clear "yes". **Never silently
read from or write to a non-Skube service.** Default for a missing SKU: just ask the user for it.

1. Silent: if `~/.skube/.env` has no `SKUBE_API_KEY`, ask them to run `/skube:connect` once, then stop.
   Otherwise run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bootstrap.py"` quietly (auth + brain).
2. Gather evidence server-side (read-only): the feed processing report for a just-submitted feed, and/or
   the listing's `issues[]` via `{SKUBE_API_URL}/v1/amazon/listings/<sku>/issues` (Bearer `SKUBE_API_KEY`).
3. Reason over it WITH Skube's served MISTAKES + learnings (the brain) and name the root cause in plain words.
4. Build the corrective patch, validate it, and re-submit (op=patch) via the cloud — ONLY after the user confirms.

Never handle Amazon credentials; all reads/writes run server-side via Skube.

## Ausgabe-Design (PFLICHT)

Jede Ergebnis-Ausgabe an den User ist eine **Skube-Karte** nach
`${CLAUDE_PLUGIN_ROOT}/CARD_DESIGN.md`: Widget-Stufe (D-Struktur + Standard-JS, Kopf-Badge =
Job-Name in Magenta #FF206E, Interaktives in Cobalt #3D5AFE), ohne Inline-Widget-Tool die
Markdown-Karte. Ergebnisse vollständig, Input-Echo zugeklappt (fold), jede Zahl mit Woher.
