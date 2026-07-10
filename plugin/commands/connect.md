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
2. It opens the Skube web app and prints a short confirmation code + a URL. Tell the user:
   "I've opened your browser — log in if needed, check the code matches, and click **Authorize**."
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

Never request, display, or write the API key yourself — the browser flow handles it end to end.
