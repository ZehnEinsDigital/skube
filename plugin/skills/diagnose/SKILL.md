---
name: diagnose
description: Find out why an Amazon SKU/listing was rejected, suppressed, errored, or isn't showing — and fix it. Use whenever the user asks why a listing failed/is suppressed/has errors/isn't live and wants it sorted.
when_to_use: 'Trigger on: "warum wurde X abgelehnt", "warum ist mein Listing unterdrückt", "SKU Y wird nicht angezeigt", "warum hat Amazon das geblockt", "fix my rejected listing", "why was my SKU rejected".'
---

Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bootstrap.py"` quietly (auth). Then fetch THIS job's
**current playbook from Skube's server and follow it EXACTLY** — the workflow lives server-side, so it stays
up to date with no plugin release:

```bash
source ~/.skube/.env 2>/dev/null
curl -s -H "Authorization: Bearer $SKUBE_API_KEY" \
  "${SKUBE_API_URL:-https://skube-api-production.up.railway.app}/v1/skills/diagnose"
```

The returned Markdown is the authoritative, always-current instructions for this job — do exactly what it
says (it may reference `${CLAUDE_PLUGIN_ROOT}/scripts/*` helpers, which this plugin provides). If the
response is empty or errors, the Skube connection isn't reachable here — tell the user to run
`/skube:connect`, then stop. **This skill is a thin shell; the logic is on the server.**
