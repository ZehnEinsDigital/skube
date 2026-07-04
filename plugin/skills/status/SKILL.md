---
name: status
description: Check the current Amazon status of a SKU/listing — what's live, suppressed, or erroring right now. Use whenever the user asks about the state of a listing or whether a SKU is online.
when_to_use: 'Trigger on: "status von SKU X", "ist mein Listing live", "was sagt Amazon zu Y", "läuft mein Produkt schon", "is my listing live", "check my SKU".'
---

Tell the user what Amazon currently says about a listing, in plain language, right here. Hide technical
detail; answer in the user's language. Never tell them to open a folder.

**Stay in Skube's lane — ask before touching anything that isn't Skube.** You may have OTHER tools or MCP
servers connected in this session (Baselinker, other marketplaces, databases, files) — those are the user's
OWN connections, NOT part of Skube. Do this with **Skube's own gateway/commands only**. If you're missing
something another connected service could supply (e.g. a SKU/EAN you don't have), **stop and ASK the user
first** — name the service and exactly what you'd pull — and use it only after a clear "yes". **Never silently
read from or write to a non-Skube service.** Default for a missing SKU: just ask the user for it.

1. Silent: if `~/.skube/.env` has no `SKUBE_API_KEY`, ask them to run `/skube:connect` once, then stop.
   Otherwise run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bootstrap.py"` quietly (auth + brain).
2. GET `{SKUBE_API_URL}/v1/amazon/listings/<sku>/issues?marketplace=DE` with Bearer `SKUBE_API_KEY`
   (read-only proxy — the server calls SP-API with the vaulted creds).
3. Summarize in plain words: what is live, suppressed, or erroring — and why.

Read-only. Never handle Amazon credentials; the call runs server-side via Skube.

## Ausgabe-Design (PFLICHT)

Jede Ergebnis-Ausgabe an den User ist eine **Skube-Karte** (`${CLAUDE_PLUGIN_ROOT}/CARD_DESIGN.md`).
**Widget-Stufe (Session hat ein Inline-Widget-Tool): NICHT selbst layouten.** Baue NUR die
Datenstruktur `D` (Schema in CARD_DESIGN.md; hier: `head.job = "Status"`, `head.icon = "list-check"`),
schreibe sie als JSON-Datei und rendere deterministisch:
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/card.py" <d.json>` → stdout ist der fertige Widget-Code.
Chat-Text danach: EIN Satz + Weiter-Zeile — Karteninhalte nie doppeln. Ohne Widget-Tool: die
Markdown-Karte aus CARD_DESIGN.md. Ergebnisse vollständig, Input-Echo/Longtail zugeklappt
(`fold: true`), jede Zahl mit Woher.
SPRACHE: English-first — Default Englisch; schreibt der User in einer anderen Sprache, ist ALLES
Nutzer-Sichtbare (Karteninhalte, `D._t`-Statuslabels, Buttons, Weiter-Zeile) konsequent in dieser
Sprache. `D._t = {"step", "ask", "done"}` in der Session-Sprache setzen (weglassen = Englisch).
