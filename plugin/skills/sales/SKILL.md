---
name: sales
description: Show real Amazon sales for the connected seller — units sold, revenue, sessions/conversion over a period. Use whenever the user asks how much they sold, sales figures, units, revenue, or a SKU/ASIN's performance on Amazon.
when_to_use: 'Trigger on: "wie viel hab ich verkauft", "Verkaufszahlen", "Amazon Sales", "Umsatz für SKU X", "wie läuft Produkt Y", "units sold", "sales for my listing", "how many did I sell", "Monatsumsatz".'
---

Fetch THIS job's
**current playbook from Skube's server and follow it EXACTLY** — the workflow lives server-side, so it stays
up to date with no plugin release:

```bash
source ~/.skube/.env 2>/dev/null
curl -s -H "Authorization: Bearer $SKUBE_API_KEY" \
  "${SKUBE_API_URL:-https://skube-api-production.up.railway.app}/v1/skills/sales"
```

**No key in this session?** (curl returns 401, or `$SKUBE_API_KEY` is empty): the account may be
linked via the Skube CONNECTOR — run ONE ToolSearch for `mint_session_key`; if found, call it
(approve the one-time permission if asked), save the key via STDIN
(`printf %s 'THE_KEY' | python3 "${CLAUDE_PLUGIN_ROOT}/scripts/save_key.py"`, never print it),
then RE-RUN the fetch above and continue. Only if that tool does not exist, tell the user (one
line): run `/skube:connect` once — then stop.

The returned Markdown is the authoritative, always-current instructions for this job — do exactly what it
says (it may reference `${CLAUDE_PLUGIN_ROOT}/scripts/*` helpers, which this plugin provides). If the
response errors for any OTHER reason, say the Skube cloud isn't reachable right now — one line, no
internals. **This skill is a thin shell; the logic is on the server.**
