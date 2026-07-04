---
name: sales
description: Show real Amazon sales for the connected seller — units sold, revenue, sessions/conversion over a period. Use whenever the user asks how much they sold, sales figures, units, revenue, or a SKU/ASIN's performance on Amazon.
when_to_use: 'Trigger on: "wie viel hab ich verkauft", "Verkaufszahlen", "Amazon Sales", "Umsatz für SKU X", "wie läuft Produkt Y", "units sold", "sales for my listing", "how many did I sell", "Monatsumsatz".'
---

Show the user their **real Amazon sales** in plain language, right here. Hide technical detail; answer in
the user's language. Never tell them to open a folder.

**Stay in Skube's lane — ask before touching anything that isn't Skube.** You may have OTHER tools or MCP
servers connected in this session (Baselinker, other marketplaces, databases, files) — those are the user's
OWN connections, NOT part of Skube. Get the sales numbers from **Skube's own Amazon endpoint** (below) — it
pulls them straight from Amazon. Do NOT silently pull sales from another connected service; if you ever need
something Skube can't give, ASK the user first (name the service + what you'd pull) and use it only after a
clear "yes".

1. Silent: if `~/.skube/.env` has no `SKUBE_API_KEY`, ask them to run `/skube:connect` once, then stop.
   Otherwise run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bootstrap.py"` quietly (auth + brain).
2. Pull the REAL numbers from Amazon — GET `{SKUBE_API_URL}/v1/amazon/sales?credential_id=<id>&marketplace=DE`
   with Bearer `SKUBE_API_KEY` (optional `&start=<ISO>&end=<ISO>`; default ≈ last 30 days). The server pulls
   Amazon's **Sales & Traffic report** with the vaulted creds and returns PII-FREE aggregates (units, revenue,
   sessions, conversion — never buyer data). If a marketplace has **>1 connection**, ask which one and pin its
   `credential_id` (same isolation as the other skills — never mix accounts).
3. If the response is **202 / `pending`**, tell the user Amazon is still generating the report (a moment) and
   retry shortly. Otherwise summarize in plain words: total **units + revenue** for the period, the **top SKUs**,
   and offer a per-SKU or per-month breakdown.

These are REAL Amazon sales (not Baselinker), PII-free, read-only. Never handle Amazon credentials; the call
runs server-side via Skube.

## Ausgabe-Design (PFLICHT)

Jede Ergebnis-Ausgabe an den User ist eine **Skube-Karte** nach
`${CLAUDE_PLUGIN_ROOT}/CARD_DESIGN.md`: Widget-Stufe (D-Struktur + Standard-JS, Kopf-Badge =
Job-Name in Magenta #FF206E, Interaktives in Cobalt #3D5AFE), ohne Inline-Widget-Tool die
Markdown-Karte. Ergebnisse vollständig, Input-Echo zugeklappt (fold), jede Zahl mit Woher.
