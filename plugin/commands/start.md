---
description: Show the Skube start card — everything you can do, one click away
argument-hint: ""
---

Show the **Skube start card** — the copilot's cockpit. It appears (a) on `/skube:start`, (b) right after a
successful `/skube:connect`, (c) on the FIRST Skube mention in a new session with no concrete job. If the
user already names a concrete job (a file + "create listings…"), do NOT show the card — execute directly.
Automatically at most once per session; on `/skube:start` always.

## 🔴 KEEP IT INSTANT — Markdown only

Render the card as **plain Markdown** (the block below). **Do NOT build an HTML / `show_widget` widget for
this card, and do NOT call `read_me`.** A widget here costs several extra tool round-trips + seconds of HTML
generation for a menu that gains nothing from it — the cockpit must be up in ~1–2 seconds. **Speed wins.**

**LANGUAGE:** English-first. If the session language differs (user writes e.g. German), translate ONLY the
visible texts — the table structure and the `/skube:*` commands stay identical.

## Determine state (silently — ONE quick check, no engine work)

- **Connected?** `~/.skube/.env` contains a `SKUBE_API_KEY` → "✅ connected". Otherwise "⏸️ not connected
  yet" and make the FIRST table row the connect row (`🔌 Connect | once, via browser | /skube:connect`).
- **Marketplaces (only if connected):** exactly ONE call — `GET $SKUBE_API_URL/v1/me/marketplaces` (Bearer
  key, 2s timeout). Mark each marketplace: `connected:true` → ✅ · `locked:false` → plain (Pro-unlocked,
  connectable, no lock) · `locked:true` → 🔒 (upsell). If the call fails/times out → fall back to
  ✅ Amazon DE · the other 13 neutral. **NEVER** label everything locked for a connected account. That is
  the ONLY network call — nothing else, no further queries.

## The card (this Markdown IS the whole output)

```markdown
## 🧊 skube — your marketplace copilot — ✅ connected

What would you like to do? Type the command — or just say it in your own words.

| Job | Just say … | Command |
|---|---|---|
| 📦 List | "list these products from my file" | `/skube:create` |
| 🔧 Fix | "why was SKU … rejected? / is it live?" | `/skube:fix` |
| 📡 Monitor | "is everything ok with my shops?" | `/skube:monitor` |
| ✏️ Update | "raise the price of SKU … everywhere" | `/skube:update` |
| ✨ Optimize | "improve my titles and bullets" | `/skube:content` |
| 📈 Report | "show my sales for the last 30 days" | `/skube:sales` |

**Marketplaces:** ✅ Amazon DE · Otto · eBay · Kaufland · MediaMarktSaturn · Metro · ManoMano · OnBuy ·
Leroy Merlin · FNAC · Cdiscount · Decathlon · Voelkner · AboutYou — mark each from `/v1/me/marketplaces`
(✅ connected · plain = Pro-unlocked/connectable · 🔒 = needs a higher tier). A Pro account shows its
marketplaces open, NOT all-locked.
**Mirakl storefronts (Voelkner · Decathlon · MediaMarktSaturn · Leroy Merlin):** these four run ON the
Mirakl platform — the user never needs to know that. Mark each ✅ iff the `mirakl` entry has a
connection whose `instance` matches (voelkner/decathlon/mediamarkt/leroymerlin). When the user picks
one to work on, pin THAT connection's `credential_id` for the run — with several Mirakl connections
choose by `instance`, never guess, never ask about "Mirakl".

**Next:** drop your product file into the chat = go · `/skube:start` shows this card anytime
```

(Not connected → heading ends "— ⏸️ not connected yet"; the first table row is
`🔌 Connect | once, via browser | /skube:connect`. Free/not-connected marketplace default: ✅ Amazon DE ·
🔒 the other 13 — "unlock with Pro".)

After the card, ONE short line max ("Where do we start?" — session language). Never repeat the card as text.

## Forbidden

No HTML / `show_widget` widget for this card (that is the whole point — speed) · no `read_me` call · no
ASCII boxes · no 7-step explanation (that belongs in the create flow) · ALWAYS write out all 14
marketplaces (never "among others") · never push the card into the middle of a running job.
