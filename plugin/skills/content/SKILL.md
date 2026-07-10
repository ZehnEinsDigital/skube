---
name: content
description: Optimize listing content — titles, bullet points, descriptions, keywords — with a before→after proposal per field, then apply as a gated partial update. Use whenever the user wants better listing copy.
when_to_use: 'Trigger on: "optimiere meine Listings", "bessere Titel", "Bullets verbessern", "SEO für meine Produkte", "Beschreibung überarbeiten", "optimize my titles", "improve my listing content", "better bullet points".'
---

Fetch THIS job's
**current playbook from Skube's server and follow it EXACTLY** — the workflow lives server-side, so it stays
up to date with no plugin release:

```bash
source ~/.skube/.env 2>/dev/null
curl -s -H "Authorization: Bearer $SKUBE_API_KEY" \
  "${SKUBE_API_URL:-https://skube-api-production.up.railway.app}/v1/skills/update"
```

Follow the returned playbook's **"CONTENT OPTIMIZATION"** section (content is an update: current-state
read → before→after card with the marketplace's own limits → gated partial update after the user's go;
several marketplaces → its MULTI-MARKETPLACE section). The returned Markdown is the authoritative,
always-current instructions — do exactly what it says (it may reference `${CLAUDE_PLUGIN_ROOT}/scripts/*`
helpers, which this plugin provides). If the response errors for any OTHER reason, say the Skube cloud isn't reachable right now — one line, no internals. **No key in this session?** (curl returns 401, or `$SKUBE_API_KEY` is empty): the account may be
linked via the Skube CONNECTOR — run ONE ToolSearch for `mint_session_key`; if found, call it
(approve the one-time permission if asked), save the key via STDIN
(`printf %s 'THE_KEY' | python3 "${CLAUDE_PLUGIN_ROOT}/scripts/save_key.py"`, never print it),
then RE-RUN the fetch above and continue. Only if that tool does not exist, tell the user (one
line): run `/skube:connect` once — then stop.

**This skill is a thin shell; the
logic is on the server.**
