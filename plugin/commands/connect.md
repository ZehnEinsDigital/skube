---
description: Connect Skube to your account via the browser (like gh login — no key to paste)
argument-hint: ""
---

One-time setup: connect this device to the user's Skube account. **Do NOT ask the user to paste
their API key.** Prefer the connector identity; fall back to the browser device-auth flow.

0. **CONNECTOR FIRST:** if this session has the Skube MCP tools (a tool named
   `mint_session_key` — the plugin bundles the Skube connector; it appears once the user has
   authorized Skube on their Claude account), skip the device flow entirely: call
   `mint_session_key`, then save the returned key via STDIN (never argv, never echo it):
   ```
   printf %s 'THE_KEY' | python3 "${CLAUDE_PLUGIN_ROOT}/scripts/save_key.py"
   ```
   Then continue at step 3's card. If the tools are NOT available (or the tool errors because the
   connector was never authorized), fall through to the device flow below.

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

**Cloud sessions — make it permanent (once per account):** if this session had NO local browser
(the script printed "open this link") and the device flow was used, the key only lives in THIS
session's sandbox. After the success line + card, offer the account-level fix in TWO short lines:
"To stay connected in every browser session, add Skube to your Claude account once:
[open the connector dialog](https://claude.ai/customize/connectors?modal=add-custom-connector&connectorName=Skube&connectorUrl=https%3A%2F%2Fskube-mcp-production.up.railway.app%2Fmcp) → Name: `Skube` · URL: `https://skube-mcp-production.up.railway.app/mcp` → Add → Authorize.
(Leave the optional OAuth fields empty — Claude registers itself.)"
The link only OPENS the dialog — the user pastes those two values. Never show this in desktop
sessions (their key persists locally).

**Output discipline (the user is a seller, not a developer):** no technical narration — before,
during, or after. Never mention hosts/URLs, config files, env vars, scripts, or memory operations.
**If the flow fails:** retry once, silently. If it still fails, say ONE plain sentence in the user's
language ("The connection didn't work — I'll report it to the Skube team.") and offer to send it via
`/skube:feedback`. Do NOT stream debugging steps or internals at the user; keep any diagnosis to
yourself unless the user explicitly asks for details.

Never request or display the API key. Device flow: the script handles the key end to end. Connector branch: pass the minted key ONLY into save_key.py via stdin and never print it in your reply.
