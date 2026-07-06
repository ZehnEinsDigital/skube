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
1b. **Pin a connection — a live status needs it.** A seller-specific status call needs the
   `credential_id` of the account; without it the gateway returns **HTTP 422 "credential_id required"**.
   NEVER guess or probe credential endpoints yourself (the credential-scanning guard will block it, rightly)
   — use ONLY the helper:
   - `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/connection.py" current` → if `pinned` is set, use it (for an
     agency account, confirm in one short line: "checking on <label> — switch?").
   - else `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/connection.py" list`:
     - exactly ONE connection → pin it silently: `connection.py pin <credential_id>`.
     - SEVERAL (an agency holds one account per client) → show the `label`s and **ASK which**, then
       `connection.py pin <credential_id>`. NEVER guess — never risk the wrong account.
     - NONE → tell them to connect a marketplace in the Skube web app, then stop.
   The pin **persists** (`~/.skube/.env`), so a later or compacted session reuses it — no re-asking.
1c. **Only a product NAME, no SKU?** Resolve it first — `GET {SKUBE_API_URL}/v1/amazon/listings/search?name=<name>&marketplace=<market>&credential_id=<pinned>` (Bearer `SKUBE_API_KEY`) → YOUR listings whose title matches, each with `sku` + `asin` + `title` + `issue_count`. One hit → use its `sku`. Several → show them and let the user pick. Only when it returns nothing, ask for the SKU. (Amazon has no name filter for a seller's own listings; Skube pages them and matches the title.)
2. GET `{SKUBE_API_URL}/v1/amazon/listings/<sku>/issues?marketplace=<market>&credential_id=<pinned>` with
   Bearer `SKUBE_API_KEY` (read-only proxy — the server calls SP-API with the vaulted creds).
3. Summarize in plain words: what is live, suppressed, or erroring — and why.

Read-only. Never handle Amazon credentials; the call runs server-side via Skube. **Don't claim "connected"
until a connection is pinned** — bootstrap/auth succeeding only means the API key resolves; a live status
still needs the pinned `credential_id`.

## Output design (MANDATORY)

Every result output to the user is a **Skube card** (`${CLAUDE_PLUGIN_ROOT}/CARD_DESIGN.md`).
**Widget tier (session has an inline-widget tool): do NOT lay it out yourself; DISPLAY it by CALLING `show_widget`** (call the visualize `read_me` once first; NEVER paste the HTML/JS into the chat as text — it won't render; see CARD_DESIGN.md "HOW TO DISPLAY IT"). Build ONLY the
data structure `D` (schema in CARD_DESIGN.md; here: `head.job = "Status"`, `head.icon = "list-check"`),
write it as a JSON file and render deterministically:
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/card.py" <d.json>` → stdout is the finished widget code.
Chat text afterwards: ONE sentence + next-step line — never duplicate card contents. Without a
widget tool: the Markdown card from CARD_DESIGN.md. Results in full, input echo/long tail collapsed
(`fold: true`), every number with its source.
LANGUAGE: English-first — default English; if the user writes in another language, EVERYTHING
user-visible (card contents, `D._t` status labels, buttons, next-step line) is consistently in that
language. Set `D._t = {"step", "ask", "done"}` in the session language (omit = English).
