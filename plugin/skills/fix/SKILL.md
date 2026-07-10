---
name: fix
description: Check a listing's current state AND fix what's wrong — one job. Reads what the marketplace says about a SKU (live, suppressed, erroring), finds the root cause, and applies the corrective patch after your go. Use whenever the user asks about a listing's state or why something was rejected/suppressed/not visible.
when_to_use: 'Trigger on: "status von SKU X", "ist mein Listing live?", "warum wurde X abgelehnt?", "warum ist mein Listing unterdrückt?", "SKU Y wird nicht angezeigt", "fix my rejected listing", "is my listing live?", "why was my SKU rejected?", "check my SKU".'
---

Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bootstrap.py"` quietly (auth). Then fetch THIS job's
**current playbook from Skube's server and follow it EXACTLY** — the workflow lives server-side, so it stays
up to date with no plugin release:

```bash
source ~/.skube/.env 2>/dev/null
curl -s -H "Authorization: Bearer $SKUBE_API_KEY" \
  "${SKUBE_API_URL:-https://skube-api-production.up.railway.app}/v1/skills/fix"
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
