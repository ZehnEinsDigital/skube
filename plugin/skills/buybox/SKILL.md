---
name: buybox
description: Buy-Box competitive analysis for the connected Amazon seller — who holds the Buy-Box on your listings, at what price you'd win it, and whether it's profitable. Produces a visual report. Use whenever the user wants a Buy-Box analysis, asks who's winning the Buy-Box, about competitors/undercutting, or repricing on their Amazon listings.
when_to_use: 'Trigger on: "Buybox Analyse", "mach mir eine Buy-Box Analyse", "wer gewinnt die Buy-Box", "verliere ich die Buybox", "wer unterbietet mich", "Buy-Box für meine SKUs", "buy box analysis", "am I winning the buy box", "who has the buy box", "competitor pricing on my listings", "repricing".'
---

Fetch THIS job's
**current playbook from Skube's server and follow it EXACTLY** — the workflow lives server-side, so it stays
up to date with no plugin release:

```bash
source ~/.skube/.env 2>/dev/null
curl -s -H "Authorization: Bearer $SKUBE_API_KEY" \
  "${SKUBE_API_URL:-https://skube-api-production.up.railway.app}/v1/skills/buybox"
```

**No key in this session?** (curl returns 401, or `$SKUBE_API_KEY` is empty): the account may be
linked via the Skube CONNECTOR — run ONE ToolSearch for `get_playbook`; if found, call it with
`buybox` and follow the returned playbook exactly: every Skube action then runs through the
Skube tools directly, and you NEVER obtain, mint, or save any credential. Only if that tool does
not exist, tell the user (one line): run `/skube:connect` once — then stop.

The returned Markdown is the authoritative, always-current instructions for this job — do exactly what it
says (it may reference `${CLAUDE_PLUGIN_ROOT}/scripts/*` helpers, which this plugin provides). If the
response errors for any OTHER reason, say the Skube cloud isn't reachable right now — one line, no
internals. **This skill is a thin shell; the logic is on the server.**
