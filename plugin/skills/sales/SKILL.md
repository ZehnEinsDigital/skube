---
name: sales
description: Show real Amazon sales for the connected seller — units sold, revenue, sessions/conversion over a period. Use whenever the user asks how much they sold, sales figures, units, revenue, or a SKU/ASIN's performance on Amazon.
when_to_use: 'Trigger on: "wie viel hab ich verkauft", "Verkaufszahlen", "Amazon Sales", "Umsatz für SKU X", "wie läuft Produkt Y", "units sold", "sales for my listing", "how many did I sell", "Monatsumsatz".'
---

Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bootstrap.py"` quietly (auth). Then fetch THIS job's
**current playbook from Skube's server and follow it EXACTLY** — the workflow lives server-side, so it stays
up to date with no plugin release:

```bash
source ~/.skube/.env 2>/dev/null
curl -s -H "Authorization: Bearer $SKUBE_API_KEY" \
  "${SKUBE_API_URL:-https://skube-api-production.up.railway.app}/v1/skills/sales"
```

The returned Markdown is the authoritative, always-current instructions for this job — do exactly what it
says (it may reference `${CLAUDE_PLUGIN_ROOT}/scripts/*` helpers, which this plugin provides). If the
response is empty or errors, the Skube connection isn't reachable here — tell the user to run
`/skube:connect`, then stop. **This skill is a thin shell; the logic is on the server.**
