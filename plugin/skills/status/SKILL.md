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

## Output design (MANDATORY)

Every result output to the user is a **Skube card** (`${CLAUDE_PLUGIN_ROOT}/CARD_DESIGN.md`).
**Widget tier (session has an inline-widget tool): do NOT lay it out yourself.** Build ONLY the
data structure `D` (schema in CARD_DESIGN.md; here: `head.job = "Status"`, `head.icon = "list-check"`),
write it as a JSON file and render deterministically:
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/card.py" <d.json>` → stdout is the finished widget code.
Chat text afterwards: ONE sentence + next-step line — never duplicate card contents. Without a
widget tool: the Markdown card from CARD_DESIGN.md. Results in full, input echo/long tail collapsed
(`fold: true`), every number with its source.
LANGUAGE: English-first — default English; if the user writes in another language, EVERYTHING
user-visible (card contents, `D._t` status labels, buttons, next-step line) is consistently in that
language. Set `D._t = {"step", "ask", "done"}` in the session language (omit = English).
