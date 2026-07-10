---
description: Connect Skube to your account via the browser (like gh login — no key to paste)
argument-hint: ""
---

One-time setup: connect this device to the user's Skube account. **Do NOT ask the user to paste
their API key.** Run the browser device-auth flow instead.

1. Run:
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/connect.py"
   ```
   (For a LOCAL test stack, prefix it with `SKUBE_API_URL="http://localhost:8000"`.)
2. The script prints the authorize URL + a short code — and states whether it could open a local
   browser. **Mirror that truthfully, and ALWAYS lead with the URL as a clickable link:**
   - Script says "open this link" (cloud/headless — no browser here): show the link + code and say
     "Click this link, log in if needed, and click **Authorize**." Never claim a browser was opened.
   - Script says "opening your browser": say so in one line — and still show the link as fallback.
3. The script waits, receives the key automatically, and saves it to `~/.skube/.env`. When it prints
   "SKUBE connected", say ONE short line ("✅ Connected." — in the user's language) and then render the **Skube start card**
   exactly as specified in `${CLAUDE_PLUGIN_ROOT}/commands/start.md` (plain Markdown — never a widget,
   never `read_me`). The card — not prose — is the onboarding: it shows every job with its command and
   the marketplaces.
4. Right after the card, ask ONCE (user's language, one line): "May Skube receive an anonymous
   run summary at the end of each run? Counters only — never product data. Helps prevent errors
   for everyone. (yes/no)". Only on an explicit yes:
   ```bash
   source ~/.skube/.env 2>/dev/null
   curl -s -X PUT -H "Authorization: Bearer $SKUBE_API_KEY" -H "Content-Type: application/json" \
     "${SKUBE_API_URL:-https://skube-api-production.up.railway.app}/v1/me/telemetry" \
     -d '{"telemetry_beacon_opt_in": true}'
   ```
   On no (or no clear answer): change nothing, never re-ask — it stays available in the Skube web
   app under Settings → Diagnostics & privacy.

**Output discipline (the user is a seller, not a developer):** no technical narration — before,
during, or after. Never mention hosts/URLs, config files, env vars, scripts, or memory operations.
**If the flow fails:** retry once, silently. If it still fails, say ONE plain sentence in the user's
language ("The connection didn't work — I'll report it to the Skube team.") and offer to send it via
`/skube:feedback`. Do NOT stream debugging steps or internals at the user; keep any diagnosis to
yourself unless the user explicitly asks for details.

Never request, display, or write the API key yourself — the browser flow handles it end to end.
