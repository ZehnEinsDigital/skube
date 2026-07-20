---
description: Connect Skube to your account via the browser (like gh login — no key to paste)
argument-hint: ""
---

One-time setup: connect this device to the user's Skube account. **Do NOT ask the user to paste
their API key.** Prefer the connector identity; fall back to the browser device-auth flow.

0. **CONNECTOR FIRST — a 5-second check, never an investigation:** connector tools are often
   DEFERRED (not in the visible list) — so do exactly ONE lookup: check your current tool list
   for `get_playbook` (scoped names look like `mcp__plugin_skube_skube__get_playbook` or
   `mcp__skube__get_playbook`), and if it's not visible, run ONE KEYWORD ToolSearch for
   `get_playbook` (never `select:` — scoped names need keyword matching). **That single search
   decides. Do NOT read plugin files, do NOT search the filesystem, do NOT deliberate — no
   result → go straight to step 1.** If the tool IS available, the ACCOUNT is already
   connected — now complete the MACHINE (Mika's onboarding ruling 17.07.: connect = make this
   computer fully ready, three mandatory steps end here):
   - `~/.skube/.env` already has a `SKUBE_API_KEY` → everything is set up. ONE line
     ("✅ All set — account and this computer are connected.") + step 3's card, STOP.
   - No key → ONE line in seller language: "Your account is connected ✓ — one more click links
     THIS computer so it can build listings." Then run step 1's script (the browser link
     flow) and continue through steps 2–3 as written. NO key talk beyond that line; the
     account connection keeps carrying every skill either way, so if the user declines or the
     link fails, they are still fully connected for everything except local listing builds —
     never block them, never nag twice in a session.

1. Run:
   ```
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/connect.py"
   ```
   (For a LOCAL test stack, prefix it with `SKUBE_API_URL="http://localhost:8000"`.)
2. The script prints the authorize URL + a short code and states truthfully whether it could open
   a local browser. **Two outcomes — mirror them exactly, ALWAYS leading with the URL as a
   clickable link:**
   - **"opening your browser"** (desktop): the script finishes on its own — say one line that the
     browser is open, show the link as fallback, and wait for its "SKUBE connected" output.
   - **"SKUBE-PENDING"** (cloud/headless — no browser here): the script has ALREADY exited so you
     can show the link. Show link + code and say "Click this link, log in if needed, and click
     **Authorize**." Never claim a browser was opened. Once the user says they approved (or right
     away, polling is harmless), run the second phase:
     ```
     python3 "${CLAUDE_PLUGIN_ROOT}/scripts/connect.py" wait
     ```
     Each `wait` call polls ~75 s. Prints "SKUBE-PENDING" again → tell the user in one short line
     you're still waiting for the Authorize click (re-show the link) and run `wait` again — up to
     ~7 times total, then treat it as expired. Prints "expired" → offer to restart with step 1.
3. On approval the key is delivered and saved automatically (`~/.skube/.env`) — never shown. When
   the script prints "SKUBE connected", say ONE short line ("✅ Connected." — in the user's language).
   **In a cloud/headless session (the SKUBE-PENDING path was used): show the "stay connected"
   connector block below IMMEDIATELY after that line — BEFORE the start card** (Mika 2026-07-17:
   after the card nobody sees or does it; as the very next click it completes the setup).
   THEN render the **Skube start card**
   exactly as specified in `${CLAUDE_PLUGIN_ROOT}/commands/start.md` (plain Markdown — never a widget,
   never `read_me`). The card — not prose — is the onboarding: it shows every job with its command and
   the marketplaces. Desktop sessions: card directly, no connector block.
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
(the script printed "open this link" / the SKUBE-PENDING path was used), the key only lives in THIS
session's sandbox. ⚠️ An "Authorize skube" dialog the session itself pops up does NOT persist in
the browser — ONLY the link below creates the durable account connector. Show this **right after
"✅ Connected." and BEFORE the start card** (never after it — buried there it never gets clicked;
Mika 2026-07-17), in TWO short lines:
"To stay connected in every browser session, add Skube to your Claude account once:
[open the connector dialog](https://claude.ai/customize/connectors?modal=add-custom-connector&connectorName=Skube&connectorUrl=https%3A%2F%2Fskube-mcp-production.up.railway.app%2Fmcp) → Name: `Skube` · URL: `https://skube-mcp-production.up.railway.app/mcp` → Add → Authorize.
(Leave the optional OAuth fields empty — Claude registers itself.)"
After they added it, add ONE more line: "Tip: in Settings → Connectors → Skube set the tools to
'Always allow' — then Skube never interrupts you with permission prompts."
On claude.ai in a browser the link opens the dialog PREFILLED (official install-link behavior);
in the desktop app's dialog the user pastes those two values — that's why both are given.
Never show this in desktop sessions (their key persists locally).

**Output discipline (the user is a seller, not a developer):** no technical narration — before,
during, or after. Never mention hosts/URLs, config files, env vars, scripts, or memory operations.
**If the flow fails:** retry once, silently. If it still fails, say ONE plain sentence in the user's
language ("The connection didn't work — I'll report it to the Skube team.") and offer to send it via
`/skube:feedback`. Do NOT stream debugging steps or internals at the user; keep any diagnosis to
yourself unless the user explicitly asks for details.

Never request or display the API key. Device flow: the script handles the key end to end. Connector branch: NO key exists at all — everything runs through the Skube tools; never create, save, or mention credentials in your reply.
