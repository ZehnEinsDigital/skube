---
description: Show the Skube start card — everything you can do, one click away
argument-hint: ""
---

Show the **Skube start card** — the copilot's cockpit. It is the SSOT for getting started and
appears (a) on `/skube:start`, (b) directly after a successful `/skube:connect`, (c) on the FIRST
Skube-related mention in a new session without a concrete job. If the user already names a concrete
job (file + "create listings…"), the card is NOT put in front — execute directly.
Show automatically at most once per session; on `/skube:start` always.

**LANGUAGE:** English-first — the card below is the English original (default). If the
session language is a different one (user writes e.g. German), translate ONLY the visible texts
into that language — layout, colors, icons and the slash commands stay exactly the same.

## Determine state (silently, without commentary)

- **Connected?** `~/.skube/.env` contains `SKUBE_API_KEY` → chip "Connected" (green). Otherwise chip
  "Not connected yet" (amber) AND, as the topmost action, a connect tile
  (button sends `/skube:connect`).
- **Marketplaces — reflect the ACCOUNT's real tier, never a hardcoded default.** When connected, call
  **`GET $SKUBE_API_URL/v1/me/marketplaces`** (Bearer key; 2s timeout) — it returns each marketplace with
  `connected` and `locked` + the account `tier`. Render each marketplace from that response:
  - `connected: true` → **✅ green** (a seller account is linked).
  - `locked: false` but not connected → **available** (a Pro-unlocked marketplace — show WITHOUT a lock,
    it's connectable), NOT a lock icon.
  - `locked: true` → **🔒** (needs a higher tier — the upsell).
  So a **Pro** account sees its unlocked marketplaces open, not all-locked. Only if the call fails/times
  out, fall back to the minimal default (Amazon DE ✅, the rest neutral) — and NEVER label everything
  locked for a connected account. (The endpoint is `/v1/me/marketplaces`; there is no plain `/v1/me`.)
- NO further queries, NO engine provisioning for the card — it must be up in seconds.

## Tier 1 — Widget (DEFAULT — when a `show_widget` tool exists in the session; the Claude Desktop app HAS it)

**Display this by CALLING the `show_widget` tool** — first call the visualize `read_me` tool once (its
setup), then pass the HTML below to `show_widget` as `widget_code`. **Do NOT print the HTML into the chat
as text** — pasted HTML does not render and the user just sees code (that was the bug). Only if no
`show_widget`/inline-widget tool exists → the Tier-2 Markdown fallback.

Build exactly this HTML — but the marketplace chips below are the **not-connected / Free default**;
**replace each chip per the `GET /v1/me/marketplaces` response** (see "Determine state"): `connected`
→ green ✅ chip, `locked:false` → neutral chip **without** a lock (Pro-unlocked, connectable), `locked:true`
→ 🔒 chip. Change nothing else (the layout is fixed so every card looks identical). The buttons send the
slash commands as a chat message (`sendPrompt`), so the right skill starts deterministically:

```html
<div style="padding:0.5rem 0;">
  <div style="display:flex; align-items:center; gap:12px; margin-bottom:6px;">
    <div style="width:40px; height:40px; display:flex; align-items:center; justify-content:center; flex:none;">
      <svg viewBox="0 0 200 200" width="34" height="34" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="skm" gradientUnits="userSpaceOnUse" x1="22" y1="22" x2="182" y2="182"><stop offset="0" stop-color="#ff206e"/><stop offset="1" stop-color="#3d5afe"/></linearGradient></defs><path fill="url(#skm)" fill-rule="evenodd" clip-rule="evenodd" d="M100 4.08718e-06L200 0V4.7619C200 17.8941 197.413 30.8977 192.388 43.0303C187.363 55.1628 179.997 66.1867 170.711 75.4726C161.425 84.7584 150.401 92.1244 138.268 97.1499C127.571 101.581 116.196 104.116 104.654 104.654C104.116 116.196 101.581 127.571 97.1499 138.268C92.1244 150.401 84.7584 161.425 75.4726 170.711C66.1867 179.997 55.1628 187.363 43.0303 192.388C30.8977 197.413 17.8941 200 4.7619 200H0V100C-4.54131e-07 86.8678 2.58658 73.8642 7.61205 61.7317C12.6375 49.5991 20.0035 38.5752 29.2893 29.2893C38.5752 20.0035 49.5991 12.6375 61.7317 7.61205C73.8642 2.58658 86.8678 4.08718e-06 100 4.08718e-06ZM104.762 95.1127C115.016 94.5723 125.116 92.2894 134.624 88.351C145.601 83.8041 155.575 77.1397 163.976 68.7382C172.378 60.3367 179.042 50.3627 183.589 39.3856C187.528 29.8775 189.81 19.778 190.351 9.52381L104.762 9.52381V95.1127ZM95.2381 9.64921V95.2381H9.64921C10.1896 84.9839 12.4725 74.8844 16.4109 65.3763C20.9578 54.3992 27.6222 44.4252 36.0237 36.0237C44.4252 27.6222 54.3992 20.9578 65.3763 16.4109C74.8844 12.4725 84.9839 10.1896 95.2381 9.64921ZM9.52381 104.762H95.1127C94.5723 115.016 92.2894 125.116 88.351 134.624C83.8041 145.601 77.1397 155.575 68.7382 163.976C60.3367 172.378 50.3627 179.042 39.3856 183.589C29.8775 187.528 19.778 189.81 9.52381 190.351V104.762ZM159.524 128.571C155.459 128.571 151.434 129.372 147.679 130.928C143.924 132.483 140.511 134.763 137.637 137.637C134.763 140.511 132.483 143.924 130.928 147.679C129.372 151.434 128.571 155.459 128.571 159.524C128.571 163.589 129.372 167.613 130.928 171.369C132.483 175.124 134.763 178.536 137.637 181.41C140.511 184.285 143.924 186.565 147.679 188.12C151.434 189.676 155.459 190.476 159.524 190.476C163.589 190.476 167.613 189.676 171.369 188.12C175.124 186.565 178.536 184.285 181.41 181.41C184.285 178.536 186.565 175.124 188.12 171.369C189.676 167.613 190.476 163.589 190.476 159.524C190.476 155.459 189.676 151.434 188.12 147.679C186.565 143.924 184.285 140.511 181.41 137.637C178.536 134.763 175.124 132.483 171.369 130.928C167.613 129.372 163.589 128.571 159.524 128.571ZM144.034 122.129C148.945 120.095 154.208 119.048 159.524 119.048C164.839 119.048 170.103 120.095 175.013 122.129C179.924 124.163 184.386 127.144 188.145 130.903C191.903 134.661 194.885 139.123 196.919 144.034C198.953 148.945 200 154.208 200 159.524C200 164.839 198.953 170.103 196.919 175.013C194.885 179.924 191.903 184.386 188.145 188.145C184.386 191.903 179.924 194.885 175.013 196.919C170.103 198.953 164.839 200 159.524 200C154.208 200 148.945 198.953 144.034 196.919C139.123 194.885 134.661 191.903 130.903 188.145C127.144 184.386 124.163 179.924 122.129 175.013C120.095 170.103 119.048 164.839 119.048 159.524C119.048 154.208 120.095 148.945 122.129 144.034C124.163 139.123 127.144 134.661 130.903 130.903C134.661 127.144 139.123 124.163 144.034 122.129Z"/></svg>
    </div>
    <div style="flex:1;">
      <div style="font-size:18px; font-weight:500; color:var(--text-primary);">skube — your marketplace copilot</div>
      <div style="font-size:13px; color:var(--text-secondary);">What would you like to do? Click an action — or just say it in your own words.</div>
    </div>
    <span style="display:inline-flex; align-items:center; gap:6px; font-size:12.5px; background:var(--bg-success); color:var(--text-success); border-radius:999px; padding:4px 12px;"><i class="ti ti-check" style="font-size:14px;" aria-hidden="true"></i>Connected</span>
  </div>

  <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:12px; margin:14px 0 16px;">
    <div style="background:var(--surface-2); border:0.5px solid var(--border); border-radius:12px; padding:0.9rem 1.1rem;">
      <div style="display:flex; align-items:center; gap:8px; margin-bottom:2px;"><i class="ti ti-packages" style="font-size:18px; color:#3D5AFE;" aria-hidden="true"></i><span style="font-size:14px; font-weight:500; color:var(--text-primary);">Create listings</span></div>
      <div style="font-size:13px; color:var(--text-secondary); margin:0 0 8px;">Build ready-to-publish listings from your product file (Excel/CSV) — Amazon account only needed for the upload.</div>
      <button onclick="sendPrompt('/skube:create')" style="font-size:13px; color:#FF206E; border:1px solid rgba(255,32,110,.5);">Create listings ↗</button>
      <div style="font-size:11.5px; font-family:var(--font-mono); color:var(--text-muted); margin-top:6px;">/skube:create</div>
    </div>
    <div style="background:var(--surface-2); border:0.5px solid var(--border); border-radius:12px; padding:0.9rem 1.1rem;">
      <div style="display:flex; align-items:center; gap:8px; margin-bottom:2px;"><i class="ti ti-list-check" style="font-size:18px; color:#3D5AFE;" aria-hidden="true"></i><span style="font-size:14px; font-weight:500; color:var(--text-primary);">Check status</span></div>
      <div style="font-size:13px; color:var(--text-secondary); margin:0 0 8px;">What's live, what's stuck, what's missing?</div>
      <button onclick="sendPrompt('/skube:status')" style="font-size:13px; color:#FF206E; border:1px solid rgba(255,32,110,.5);">Show status ↗</button>
      <div style="font-size:11.5px; font-family:var(--font-mono); color:var(--text-muted); margin-top:6px;">/skube:status</div>
    </div>
    <div style="background:var(--surface-2); border:0.5px solid var(--border); border-radius:12px; padding:0.9rem 1.1rem;">
      <div style="display:flex; align-items:center; gap:8px; margin-bottom:2px;"><i class="ti ti-stethoscope" style="font-size:18px; color:#3D5AFE;" aria-hidden="true"></i><span style="font-size:14px; font-weight:500; color:var(--text-primary);">Find the problem</span></div>
      <div style="font-size:13px; color:var(--text-secondary); margin:0 0 8px;">Listing rejected or not visible? Find the cause — and fix it.</div>
      <button onclick="sendPrompt('/skube:diagnose')" style="font-size:13px; color:#FF206E; border:1px solid rgba(255,32,110,.5);">Find the cause ↗</button>
      <div style="font-size:11.5px; font-family:var(--font-mono); color:var(--text-muted); margin-top:6px;">/skube:diagnose</div>
    </div>
    <div style="background:var(--surface-2); border:0.5px solid var(--border); border-radius:12px; padding:0.9rem 1.1rem;">
      <div style="display:flex; align-items:center; gap:8px; margin-bottom:2px;"><i class="ti ti-edit" style="font-size:18px; color:#3D5AFE;" aria-hidden="true"></i><span style="font-size:14px; font-weight:500; color:var(--text-primary);">Update a listing</span></div>
      <div style="font-size:13px; color:var(--text-secondary); margin:0 0 8px;">Change title, bullets, description or attributes — without rebuilding.</div>
      <button onclick="sendPrompt('/skube:update')" style="font-size:13px; color:#FF206E; border:1px solid rgba(255,32,110,.5);">Update listing ↗</button>
      <div style="font-size:11.5px; font-family:var(--font-mono); color:var(--text-muted); margin-top:6px;">/skube:update</div>
    </div>
    <div style="background:var(--surface-2); border:0.5px solid var(--border); border-radius:12px; padding:0.9rem 1.1rem;">
      <div style="display:flex; align-items:center; gap:8px; margin-bottom:2px;"><i class="ti ti-chart-bar" style="font-size:18px; color:#3D5AFE;" aria-hidden="true"></i><span style="font-size:14px; font-weight:500; color:var(--text-primary);">See sales</span></div>
      <div style="font-size:13px; color:var(--text-secondary); margin:0 0 8px;">Units, revenue and conversion — straight from Amazon.</div>
      <button onclick="sendPrompt('/skube:sales')" style="font-size:13px; color:#FF206E; border:1px solid rgba(255,32,110,.5);">Show sales ↗</button>
      <div style="font-size:11.5px; font-family:var(--font-mono); color:var(--text-muted); margin-top:6px;">/skube:sales</div>
    </div>
  </div>

  <div style="margin-bottom:14px;">
    <div style="font-size:13px; color:var(--text-secondary); margin-bottom:8px;">Your marketplaces</div>
    <div style="display:flex; flex-wrap:wrap; gap:6px;">
      <span style="display:inline-flex; align-items:center; gap:5px; font-size:12.5px; background:var(--bg-success); color:var(--text-success); border-radius:999px; padding:3px 10px;"><i class="ti ti-check" style="font-size:13px;" aria-hidden="true"></i>Amazon DE</span>
      <span style="display:inline-flex; align-items:center; gap:5px; font-size:12.5px; color:var(--text-muted); border:0.5px solid var(--border); border-radius:999px; padding:3px 10px;"><i class="ti ti-lock" style="font-size:13px;" aria-hidden="true"></i>Otto Market</span>
      <span style="display:inline-flex; align-items:center; gap:5px; font-size:12.5px; color:var(--text-muted); border:0.5px solid var(--border); border-radius:999px; padding:3px 10px;"><i class="ti ti-lock" style="font-size:13px;" aria-hidden="true"></i>eBay</span>
      <span style="display:inline-flex; align-items:center; gap:5px; font-size:12.5px; color:var(--text-muted); border:0.5px solid var(--border); border-radius:999px; padding:3px 10px;"><i class="ti ti-lock" style="font-size:13px;" aria-hidden="true"></i>Kaufland</span>
      <span style="display:inline-flex; align-items:center; gap:5px; font-size:12.5px; color:var(--text-muted); border:0.5px solid var(--border); border-radius:999px; padding:3px 10px;"><i class="ti ti-lock" style="font-size:13px;" aria-hidden="true"></i>MediaMarktSaturn</span>
      <span style="display:inline-flex; align-items:center; gap:5px; font-size:12.5px; color:var(--text-muted); border:0.5px solid var(--border); border-radius:999px; padding:3px 10px;"><i class="ti ti-lock" style="font-size:13px;" aria-hidden="true"></i>Metro Markets</span>
      <span style="display:inline-flex; align-items:center; gap:5px; font-size:12.5px; color:var(--text-muted); border:0.5px solid var(--border); border-radius:999px; padding:3px 10px;"><i class="ti ti-lock" style="font-size:13px;" aria-hidden="true"></i>ManoMano</span>
      <span style="display:inline-flex; align-items:center; gap:5px; font-size:12.5px; color:var(--text-muted); border:0.5px solid var(--border); border-radius:999px; padding:3px 10px;"><i class="ti ti-lock" style="font-size:13px;" aria-hidden="true"></i>OnBuy</span>
      <span style="display:inline-flex; align-items:center; gap:5px; font-size:12.5px; color:var(--text-muted); border:0.5px solid var(--border); border-radius:999px; padding:3px 10px;"><i class="ti ti-lock" style="font-size:13px;" aria-hidden="true"></i>Leroy Merlin</span>
      <span style="display:inline-flex; align-items:center; gap:5px; font-size:12.5px; color:var(--text-muted); border:0.5px solid var(--border); border-radius:999px; padding:3px 10px;"><i class="ti ti-lock" style="font-size:13px;" aria-hidden="true"></i>FNAC</span>
      <span style="display:inline-flex; align-items:center; gap:5px; font-size:12.5px; color:var(--text-muted); border:0.5px solid var(--border); border-radius:999px; padding:3px 10px;"><i class="ti ti-lock" style="font-size:13px;" aria-hidden="true"></i>Cdiscount</span>
      <span style="display:inline-flex; align-items:center; gap:5px; font-size:12.5px; color:var(--text-muted); border:0.5px solid var(--border); border-radius:999px; padding:3px 10px;"><i class="ti ti-lock" style="font-size:13px;" aria-hidden="true"></i>Decathlon</span>
      <span style="display:inline-flex; align-items:center; gap:5px; font-size:12.5px; color:var(--text-muted); border:0.5px solid var(--border); border-radius:999px; padding:3px 10px;"><i class="ti ti-lock" style="font-size:13px;" aria-hidden="true"></i>Voelkner</span>
      <span style="display:inline-flex; align-items:center; gap:5px; font-size:12.5px; color:var(--text-muted); border:0.5px solid var(--border); border-radius:999px; padding:3px 10px;"><i class="ti ti-lock" style="font-size:13px;" aria-hidden="true"></i>AboutYou</span>
      <button onclick="sendPrompt('What do I get with Skube Pro?')" style="font-size:12.5px; padding:3px 12px; border-radius:999px; color:#3D5AFE; border:1px solid rgba(61,90,254,.35);">Unlock with Pro ↗</button>
    </div>
  </div>

  <div style="display:flex; align-items:center; gap:8px; font-size:13px; color:var(--text-muted);">
    <i class="ti ti-message" style="font-size:16px;" aria-hidden="true"></i>
    <span>You can also just ask — for example <a href="#" onclick="event.preventDefault(); sendPrompt('Which Amazon category fits box spring beds?')" style="color:#3D5AFE;">"Which category fits box spring beds?"</a> · This card: /skube:start</span>
  </div>
</div>
```

Not-connected variant: status chip → `background:var(--bg-warning); color:var(--text-warning)`
with text "Not connected yet", and BEFORE the action grid one tile "Connect once — opens your
browser briefly, no key to paste" with `<button onclick="sendPrompt('/skube:connect')">Connect ↗</button>`.

After the widget, the chat text is ONE short line ("Where do we start?" — session language) —
never repeat the card contents as text.

## Tier 2 — Markdown fallback (no widget tool in the session)

```markdown
## 🧊 skube — your marketplace copilot — ✅ connected

What would you like to do? Type the command — or just say it in your own words.

| Job | Just say … | Command |
|---|---|---|
| 📦 Create listings | "create listings from my file" | `/skube:create` |
| ✅ Check status | "what's going on with my listings?" | `/skube:status` |
| 🩺 Find the problem | "why isn't my listing visible?" | `/skube:diagnose` |
| ✏️ Update a listing | "change the title of SKU …" | `/skube:update` |
| 📈 See sales | "show my sales for the last 30 days" | `/skube:sales` |

**Marketplaces:** list ALL 14, marked from `GET /v1/me/marketplaces` — ✅ for `connected`, plain (no lock)
for Pro-unlocked (`locked:false`), 🔒 only for `locked:true` (upsell). A Pro account therefore shows its
unlocked marketplaces open, NOT all-locked. Free/not-connected default: ✅ Amazon DE · 🔒 the other 13 —
"unlock with Pro". (Never hardcode all-locked for a connected account.)

**Next:** drop your product file into the chat = go · `/skube:start` shows this card anytime
```

(Not connected: heading "— ⏸️ not connected yet", first table row
"🔌 Connect | once, via browser | `/skube:connect`".)

## Forbidden

No ASCII boxes · no 7-step explanation on this card (that belongs in the create flow) ·
ALWAYS write out all 14 marketplaces (never "among others") · never push the card into the middle
of a running job.
