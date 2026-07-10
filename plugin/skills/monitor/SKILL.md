---
name: monitor
description: Monitor all connected marketplaces — connections, active offers, problems — as one read-only digest card. Use whenever the user wants the overall picture of their channels without naming a specific SKU.
when_to_use: 'Trigger on: "alles ok?", "wie läuft mein Business?", "wie stehen meine Shops?", "channel health", "monitor my channels", "is everything ok?", "overall status", "check all marketplaces".'
---

Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bootstrap.py"` quietly (auth). Then fetch THIS job's
**current playbook from Skube's server and follow it EXACTLY** — the workflow lives server-side, so it stays
up to date with no plugin release:

```bash
source ~/.skube/.env 2>/dev/null
curl -s -H "Authorization: Bearer $SKUBE_API_KEY" \
  "${SKUBE_API_URL:-https://skube-api-production.up.railway.app}/v1/skills/monitor"
```

The returned Markdown is the authoritative, always-current instructions for this job — do exactly what it
says (it may reference `${CLAUDE_PLUGIN_ROOT}/scripts/*` helpers, which this plugin provides). If the
response is empty or errors, the Skube connection isn't reachable here — tell the user to run
`/skube:connect`, then stop. **This skill is a thin shell; the logic is on the server.**
