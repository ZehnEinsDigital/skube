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
   - **Only a product NAME, no SKU?** Resolve it first — `GET {SKUBE_API_URL}/v1/amazon/listings/search?name=<name>&marketplace=<mkt>&credential_id=<pinned>` (Bearer `SKUBE_API_KEY`) returns YOUR listings whose title matches, each with `sku` + `asin` + `title` + `issue_count`. One hit → use its `sku`. Several → show the candidates and let the user pick. Only when the search returns nothing, ask the user for the SKU. (Amazon has no name filter for a seller's own listings; Skube pages them and matches the title.)
2. Gather evidence server-side (read-only): the feed processing report for a just-submitted feed, and/or
   the listing's `issues[]` via `{SKUBE_API_URL}/v1/amazon/listings/<sku>/issues` (Bearer `SKUBE_API_KEY`).
3. Reason over it WITH Skube's served MISTAKES + learnings (the brain) and name the root cause in plain words.
4. Build the corrective patch, validate it, and re-submit (op=patch) via the cloud — ONLY after the user confirms.

Never handle Amazon credentials; all reads/writes run server-side via Skube.

## Output design (MANDATORY)

Every result output to the user is a **Skube card** (`${CLAUDE_PLUGIN_ROOT}/CARD_DESIGN.md`).
**Widget tier (session has an inline-widget tool): do NOT lay it out yourself; DISPLAY it by CALLING `show_widget`** (call the visualize `read_me` once first; NEVER paste the HTML/JS into the chat as text — it won't render; see CARD_DESIGN.md "HOW TO DISPLAY IT"). Build ONLY the
data structure `D` (schema in CARD_DESIGN.md; here: `head.job = "Diagnosis"`, `head.icon = "stethoscope"`),
write it as a JSON file and render deterministically:
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/card.py" <d.json>` → stdout is the finished widget code.
Chat text afterwards: ONE sentence + next-step line — never duplicate card contents. Without a
widget tool: the Markdown card from CARD_DESIGN.md. Results in full, input echo/long tail collapsed
(`fold: true`), every number with its source.
LANGUAGE: English-first — default English; if the user writes in another language, EVERYTHING
user-visible (card contents, `D._t` status labels, buttons, next-step line) is consistently in that
language. Set `D._t = {"step", "ask", "done"}` in the session language (omit = English).
