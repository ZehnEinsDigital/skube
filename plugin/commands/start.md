---
description: Show the Skube start card — everything you can do, one click away
argument-hint: ""
---

Show the **Skube start card** — the copilot's cockpit. It appears (a) on `/skube:start`, (b) right after a
successful `/skube:connect`, (c) on the FIRST Skube mention in a new session with no concrete job. If the
user already names a concrete job (a file + "create listings…"), do NOT show the card — execute directly.
Automatically at most once per session; on `/skube:start` always.

## 🔴 KEEP IT INSTANT — ONE call, paste verbatim

The card comes **FINISHED from the server** (86catdj5z — live-measured: hand-composing it cost
~2 minutes; the one-call path costs seconds). **Do NOT build an HTML / `show_widget` widget, do
NOT call `read_me`, do NOT fetch `/v1/me/marketplaces`, do NOT re-render, translate, or edit the
fetched card.** Paste it exactly as returned. **Speed wins.**

## The flow (silently)

1. **Connected? CONNECTOR FIRST, unconditionally** (live incidents 17.07.: one session checked
   only the key file; another had the connector but a STALE cached tool list without
   `get_start_card` — both rendered a false "not connected"; the card must never lie): ONE
   ToolSearch with the plain KEYWORD query `get_start_card` — **never `select:` — connector
   tools carry long scoped names (like `mcp__<id>__get_start_card`) and only keyword search
   matches them** (live incident #4: `select:get_start_card` returned nothing while the tool
   sat in the list). Not found → ONE keyword ToolSearch for `get_playbook`. **EITHER
   found → connected via the connector** (tool-first; no key is ever created or saved):
   `get_start_card` available → step 2's connector branch; only `get_playbook` available (the
   app is holding an older tool snapshot) → render the FALLBACK card below in its CONNECTED
   form and add one line: "Tip: in Settings → Connectors → Skube choose 'Refresh tools list' —
   the cockpit gets faster." Neither tool → check `~/.skube/.env` for `SKUBE_API_KEY` →
   connected (keyed). Nothing at all → **not connected**: render the not-connected variant of
   the fallback card and stop. The key matters ONLY for local engine runs — a missing key
   alone NEVER means "not connected".
2. **Fetch the card — exactly ONE call** (pass the session language, `en` or `de`):
   - Connector session: call the `get_start_card` tool → paste `markdown` verbatim.
   - Keyed session: `curl -sf -m 5 -H "Authorization: Bearer $SKUBE_API_KEY"
     "$SKUBE_API_URL/v1/skills/start-card?language=<lang>"` → paste the body verbatim
     (`-f` = an auth error yields empty output → step 3, never a pasted error body).
   An `en`/`de` card is pasted EXACTLY as returned — never translated or edited. ONLY for other
   session languages: paste the English card, then translate the visible texts — table
   structure and `/skube:*` commands stay identical.
3. **Only if that call fails/times out:** render the FALLBACK card below (✅ Amazon DE · the
   other 12 neutral — **NEVER** all-locked for a connected account).

## FALLBACK card (offline/not-connected only — the server card is the normal path)

```markdown
## 🧊 skube — your marketplace copilot — ✅ connected

What would you like to do? Type the command — or just say it in your own words.

| Skill | Just say … | Command |
|---|---|---|
| 📦 List | "list these products from my file" | `/skube:create` |
| 🔧 Fix | "why was SKU … rejected? / is it live?" | `/skube:fix` |
| 📡 Monitor | "is everything ok with my shops?" | `/skube:monitor` |
| ✏️ Update | "raise the price of SKU … everywhere" | `/skube:update` |
| ✨ Optimize | "improve my titles and bullets" | `/skube:content` |
| 📈 Report | "show my sales for the last 30 days" | `/skube:sales` |

**Marketplaces:** ✅ Amazon DE · Otto · eBay · Kaufland · MediaMarktSaturn · Metro · ManoMano · OnBuy ·
Leroy Merlin · Cdiscount · Decathlon · Voelkner · AboutYou
*(✅ = connected · plain = ready to connect anytime)*

**Next:** drop your product file into the chat = go · `/skube:start` shows this card anytime ·
💬 `/skube:feedback` sends your words to the Skube team
```

(Not connected → heading ends "— ⏸️ not connected yet"; the first table row is
`🔌 Connect | once, via browser | /skube:connect`. Marketplace default when not connected:
✅ Amazon DE · the other 12 plain — every tier may connect; locks only ever come from the
server card.)

After the card, ONE short line max ("Where do we start?" — session language). Never repeat the card as text.

**Mirakl storefronts (Voelkner · Decathlon · MediaMarktSaturn · Leroy Merlin):** these four run ON the
Mirakl platform — the user never needs to know that. When the user picks one to work on, pin THAT
connection's `credential_id` for the run — with several Mirakl connections choose by `instance`,
never guess, never ask about "Mirakl".

## Forbidden

No HTML / `show_widget` widget for this card (that is the whole point — speed) · no `read_me` call · no
ASCII boxes · no 7-step explanation (that belongs in the create flow) · ALWAYS write out all 13
marketplaces (never "among others") · never push the card into the middle of a running job.
