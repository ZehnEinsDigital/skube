---
name: update
description: Change the content of existing Amazon listings (title, bullets, description, attributes) without recreating them — preserves the ASIN and reviews. Use whenever the user wants to edit/update/change an existing listing.
when_to_use: 'Trigger on: "ändere die Beschreibung von X", "update den Titel von Y", "passe Listing Z an", "korrigiere die Bullets bei X", "update my listing", "change the title of SKU Y".'
---

Apply a partial content update to existing listings, right here in this chat — never delete + recreate.
Hide technical detail; answer in the user's language. Never tell them to open a folder.

**Stay in Skube's lane — ask before touching anything that isn't Skube.** You may have OTHER tools or MCP
servers connected in this session (Baselinker, other marketplaces, databases, files) — those are the user's
OWN connections, NOT part of Skube. Do this with **Skube's own gateway/commands only**. If you're missing
something another connected service could supply (e.g. a SKU/EAN you don't have), **stop and ASK the user
first** — name the service and exactly what you'd pull — and use it only after a clear "yes". **Never silently
read from or write to a non-Skube service.** Default for a missing SKU: just ask the user for it.

1. Silent: if `~/.skube/.env` has no `SKUBE_API_KEY`, ask them to run `/skube:connect` once, then stop.
   Otherwise run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bootstrap.py"` quietly (auth + brain). Use the
   exported `$SKUBE_ENGINE_DIR`; if it is **unset** (the env-file export isn't available in every
   environment), read the machine-readable `SKUBE_ENGINE_DIR=<path>` line bootstrap printed as its last
   stdout line and use that path wherever `$SKUBE_ENGINE_DIR` appears below.
   - **Brand-wide update** ("update all NordPure listings")? Recall the baseline from the run-memory:
     `curl -s -H "Authorization: Bearer $SKUBE_API_KEY"
     "$SKUBE_API_URL/v1/runs?brand=<brand>&marketplace=<marketplace>"`, then download the newest run's
     `listings` (`…/v1/runs/<run_id>/artifacts/listings/download`) — it's what was created, keyed by SKU/EAN,
     i.e. your set of SKUs + their prior values to patch against. For a single named SKU, skip this.
2. For each SKU, read its current state via the status proxy, then build a JSON-Patch payload (only the
   attributes to change) — use the engine from `$SKUBE_ENGINE_DIR` with the gateway env (SKUBE_GATEWAY=true,
   the `_gateway_shim` on PYTHONPATH, key/url from `~/.skube/.env`).
3. Validate via `{SKUBE_API_URL}/v1/amazon/validate` (op=patch); fix any issues.
4. Submit via `{SKUBE_API_URL}/v1/amazon/submit` (op=patch) — only after the user confirms.

Partial update (UPDATE_PARTIAL), never delete. Never handle Amazon credentials; runs server-side via Skube.

## Ausgabe-Design (PFLICHT)

Jede Ergebnis-Ausgabe an den User ist eine **Skube-Karte** nach
`${CLAUDE_PLUGIN_ROOT}/CARD_DESIGN.md`: Widget-Stufe (D-Struktur + Standard-JS, Kopf-Badge =
Job-Name in Magenta #FF206E, Interaktives in Cobalt #3D5AFE), ohne Inline-Widget-Tool die
Markdown-Karte. Ergebnisse vollständig, Input-Echo zugeklappt (fold), jede Zahl mit Woher.
