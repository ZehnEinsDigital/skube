---
description: Show the Skube start card — everything you can do, one click away
argument-hint: ""
---

Zeige die **Skube-Start-Karte** — das Cockpit des Kopiloten. Sie ist die SSOT für den Einstieg und
erscheint (a) auf `/skube:start`, (b) direkt nach erfolgreichem `/skube:connect`, (c) beim ERSTEN
Skube-Bezug einer neuen Session ohne konkreten Auftrag. Nennt der Nutzer bereits einen konkreten
Auftrag (Datei + „erstelle Listings…"), wird die Karte NICHT vorgeschaltet — direkt ausführen.
Maximal einmal pro Session automatisch zeigen; auf `/skube:start` immer.

**SPRACHE:** English-first — die Karte unten ist das englische Original (Default). Ist die
Session-Sprache eine andere (User schreibt z. B. Deutsch), übersetze NUR die sichtbaren Texte
in diese Sprache — Layout, Farben, Icons und die Slash-Befehle bleiben exakt gleich.

## Zustand bestimmen (still, ohne Kommentar)

- **Verbunden?** `~/.skube/.env` enthält `SKUBE_API_KEY` → Chip „Verbunden" (grün). Sonst Chip
  „Noch nicht verbunden" (amber) UND als oberste Aktion eine Verbinden-Kachel
  (Button sendet `/skube:connect`).
- **Marktplätze:** Standard: Amazon DE aktiv, alle 13 anderen gesperrt. Wenn verbunden und die
  Antwort von `GET $SKUBE_API_URL/v1/me` schnell verfügbar ist (2s-Timeout, sonst Standard nehmen),
  die tatsächlich freigeschalteten Marktplätze mit Haken markieren.
- KEINE weiteren Abfragen, KEIN Engine-Provisioning für die Karte — sie muss in Sekunden stehen.

## Stufe 1 — Widget (wenn die Session ein Inline-Widget-Tool hat, z. B. `show_widget`)

Genau dieses HTML rendern (Status-Chip und Marktplatz-Haken an den Zustand anpassen, sonst nichts
ändern — Layout ist fix, damit jede Karte identisch aussieht). Die Buttons senden die
Slash-Befehle als Chat-Nachricht (`sendPrompt`), damit deterministisch der richtige Skill startet:

```html
<div style="padding:0.5rem 0;">
  <div style="display:flex; align-items:center; gap:12px; margin-bottom:6px;">
    <div style="width:40px; height:40px; border-radius:10px; background:#FF206E; display:flex; align-items:center; justify-content:center;">
      <i class="ti ti-cube" style="font-size:22px; color:#fff;" aria-hidden="true"></i>
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

## Stufe 2 — Markdown-Fallback (kein Widget-Tool in der Session)

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

**Marketplaces:** ✅ Amazon DE · 🔒 Otto Market, eBay, Kaufland, MediaMarktSaturn, Metro Markets, ManoMano, OnBuy, Leroy Merlin, FNAC, Cdiscount, Decathlon, Voelkner, AboutYou — unlock with Pro

**Next:** drop your product file into the chat = go · `/skube:start` shows this card anytime
```

(Not connected: heading "— ⏸️ not connected yet", first table row
"🔌 Connect | once, via browser | `/skube:connect`".)

## Verbote

Keine ASCII-Boxen · keine 7-Schritte-Erklärung auf dieser Karte (die gehört in den Create-Flow) ·
Marktplätze IMMER alle 14 ausschreiben (nie „u. a.") · Karte nie mitten in einen laufenden
Auftrag schieben.
