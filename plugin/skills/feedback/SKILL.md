---
name: feedback
description: Send the user's feedback (praise, gripe, feature wish, bug story) to the Skube team. Use when the user wants to tell Skube something — never auto-send anything they didn't say.
when_to_use: 'Trigger on: "/skube:feedback", "Feedback an Skube", "das nervt", "wünsche mir", "feature request", "send feedback", "tell the Skube team", "report this to skube".'
---

Fetch THIS job's
**current playbook from Skube's server and follow it EXACTLY** — the workflow lives server-side, so it stays
up to date with no plugin release:

```bash
source ~/.skube/.env 2>/dev/null
curl -s -H "Authorization: Bearer $SKUBE_API_KEY" \
  "${SKUBE_API_URL:-https://skube-api-production.up.railway.app}/v1/skills/feedback"
```

The returned Markdown is the authoritative, always-current instructions for this job — do exactly what it
says. If the response errors for any OTHER reason, say the Skube cloud isn't reachable right now — one line, no internals. **No key in this session?** (curl returns 401, or `$SKUBE_API_KEY` is empty): the account may be
linked via the Skube CONNECTOR — run ONE ToolSearch for `get_playbook`; if found, call it with
`feedback` and follow the returned playbook exactly: every Skube action then runs through the
Skube tools directly, and you NEVER obtain, mint, or save any credential. Only if that tool does
not exist, tell the user (one line): run `/skube:connect` once — then stop.

**This skill is a thin shell; the logic is on the server.**
