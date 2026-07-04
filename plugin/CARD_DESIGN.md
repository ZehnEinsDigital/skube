# Skube-Karten-Design — EIN Look für ALLE Job-Ausgaben

Jede Ergebnis-Ausgabe an den User (status, diagnose, update, sales — und alles Künftige) ist eine
**Skube-Karte** in genau diesem Design. Die Checkpoint-Karten des Create-Flows rendert
`core/render_card.py` deterministisch — dieses Dokument ist der **Spiegel** desselben Designs für
Karten, deren Inhalt der Agent selbst zusammenstellt. Ändert sich das Design, gilt: `render_card.py`
ist die SSOT, diese Datei zieht nach.

## Markenfarben (fest)

| Rolle | Farbe | Einsatz |
|---|---|---|
| Hauptfarbe | `#FF206E` (Magenta) | Kopf-Badge (Job/Schritt), primäre Aktions-Buttons |
| Zweitfarbe | `#3D5AFE` (Cobalt) | Sektions-Punkt, sekundäre Buttons, Aufklapp-Buttons, Icons, Links |
| Status | grün `#1a6b3c`/`#e3f2e8` · amber `#8a5a00`/`#fdf0d5` | NUR Zustand (fertig / braucht Antwort) — nie für Deko |

Regeln: Magenta = „das ist die Aktion / das ist Skube". Cobalt = „das ist klickbar/interaktiv".
Status bleibt semantisch. Sonst Host-Variablen (`var(--text-primary)` usw.) — nie Hardcode-Grau.

## Widget-Stufe (Session hat ein Inline-Widget-Tool)

Karte = `<div id="sk-card">` + `<script>` mit einer Datenstruktur `D` + dem Standard-JS unten.
Der Agent baut NUR `D` — das Layout kommt aus dem JS, dadurch sieht jede Karte identisch aus.

**Empfohlener Weg — nicht abtippen:** `D` als JSON-Datei schreiben und deterministisch rendern:
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/card.py" <d.json>` → stdout ist der fertige Widget-Code
(das Skript liest das Standard-JS unten aus dieser Datei; der Release-Build spiegelt es
automatisch aus `render_card.py`). Das JS unten nur dann 1:1 übernehmen, wenn Python in der
Session nicht verfügbar ist.

```js
D = {
  head: { icon: "chart-bar", emoji: "📊", job: "Verkäufe", title: "Amazon DE · 30 Tage", status: "done" },
        // icon = Tabler-Outline-Name (Magenta-Kachel); status: "done" | "ask";
        // Create-Flow nutzt step:"1/7" statt job. emoji nur für den Markdown-Fallback.
  chips: [ { v: "1.204", l: "Einheiten" }, { v: "89.312 €", l: "Umsatz" } ],   // Kennzahlen
  _t: { step: "Step", ask: "⏸️ needs your answer", done: "✅ done" },  // Statuslabels — in Session-Sprache setzen; weglassen = Englisch
  sections: [
    { t: "table", title: "…", cols: ["Was","Ergebnis","Woher"], rows: [[…]] },
    { t: "table", title: "Alle N … anzeigen", fold: true, cols: […], rows: [[…]] },  // Input-Echo/Longtail
    { t: "tree",  title: "…", text: "Serie …\n ├─ …" },
    { t: "buttons", title: "Zu klären", note: "…", items: [
        { label: "…", prompt: "…", primary: true } ] }        // primary = Magenta, sonst Cobalt
  ]
}
```

Standard-JS (Spiegel von `render_card.py` — 1:1 übernehmen, nicht umbauen):

```html
<div id="sk-card" style="padding:0.5rem 0"></div>
<script>
const D={/* … vom Agent gebaut … */};
const B1='#FF206E',B2='#3D5AFE';
const BR='var(--border,rgba(127,127,127,.3))',BRS='rgba(127,127,127,.18)',SF='var(--surface-1,rgba(127,127,127,.08))';
const E=s=>String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const host=document.getElementById('sk-card');
function card(inner){return `<div style="background:var(--surface-2,transparent);border:0.5px solid ${BR};border-radius:12px;padding:12px 16px;margin:12px 0">${inner}</div>`}
function chips(c){return `<div style="display:flex;gap:10px;flex-wrap:wrap;margin:14px 0 4px 0">`+c.map(x=>`<div style="background:${SF};border-radius:10px;padding:10px 18px;min-width:90px"><div style="font-size:22px;font-weight:500;color:${x.c||'var(--text-primary)'}">${E(x.v)}</div><div style="font-size:12px;color:var(--text-secondary)">${E(x.l)}</div></div>`).join('')+`</div>`}
function table(s,i){const th=s.cols.map(c=>`<th style="padding:6px 10px 6px 0;font-weight:500;text-align:left">${E(c)}</th>`).join('');
 const tr=s.rows.map(r=>`<tr style="border-bottom:1px solid ${BRS}">`+r.map((c,i)=>`<td style="padding:6px 10px 6px 0;color:${i===0?'var(--text-primary)':'var(--text-secondary)'};font-size:13.5px">${c==null?'':(s.html?String(c):E(c))}</td>`).join('')+`</tr>`).join('');
 const tbl=`<div style="overflow-x:auto"><table style="border-collapse:collapse;width:100%"><thead><tr style="border-bottom:1px solid ${BR};color:var(--text-secondary)">${th}</tr></thead><tbody>${tr}</tbody></table></div>`;
 if(!s.fold)return card(sec(s.title)+tbl);
 return card(`<button onclick="skFold(${i},this)" style="font-family:inherit;font-size:13.5px;border:1px solid rgba(61,90,254,.35);color:${B2};background:transparent;border-radius:8px;padding:6px 14px;cursor:pointer"><span>▸ </span>${E(s.title)}</button><div id="skf${i}" style="display:none">${tbl}</div>`)}
window.skFold=(i,btn)=>{const d=document.getElementById('skf'+i);const open=d.style.display==='none';d.style.display=open?'':'none';btn.firstChild.textContent=open?'▾ ':'▸ ';};
function tree(s){return card(sec(s.title)+`<pre style="font-size:12.5px;line-height:1.55;background:${SF};border-radius:10px;padding:12px 14px;overflow-x:auto;margin:4px 0">${E(s.text)}</pre>`)}
function sec(t){return t?`<div style="font-size:15px;font-weight:500;color:var(--text-primary);margin:0 0 8px 0"><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${B2};margin-right:8px;vertical-align:1px"></span>${E(t)}</div>`:''}
function buttons(s){return card(`<div style="font-size:15px;font-weight:500;color:var(--text-primary);margin-bottom:6px"><span style="display:inline-block;width:8px;height:8px;border-radius:2px;background:${B1};margin-right:8px;vertical-align:1px"></span>${E(s.title)}</div>${s.note?`<div style="font-size:13.5px;color:var(--text-secondary);margin-bottom:10px">${E(s.note)}</div>`:''}<div style="display:flex;gap:8px;flex-wrap:wrap">`+s.items.map(b=>`<button onclick="sendPrompt(${JSON.stringify(b.prompt)})" style="font-family:inherit;font-size:13.5px;border:1px solid ${b.primary?'rgba(255,32,110,.5)':'rgba(61,90,254,.35)'};color:${b.primary?B1:B2};background:transparent;border-radius:8px;padding:6px 14px;cursor:pointer">${E(b.label)}</button>`).join('')+`</div>`)}
const T=Object.assign({step:'Step',ask:'⏸️ needs your answer',done:'✅ done'},D._t||{});
const stat=D.head.status==='ask'?[T.ask,'#8a5a00','#fdf0d5']:[T.done,'#1a6b3c','#e3f2e8'];
let h=`<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap"><div style="width:40px;height:40px;border-radius:10px;background:${B1};display:flex;align-items:center;justify-content:center;flex:none"><i class="ti ti-${D.head.icon||'cube'}" style="font-size:22px;color:#fff" aria-hidden="true"></i></div><div style="flex:1;min-width:180px"><div style="font-size:18px;font-weight:500;color:var(--text-primary)">${E(D.head.title)}</div><div style="font-size:12.5px;color:var(--text-secondary)">${E(D.head.step?T.step+' '+D.head.step:D.head.job||'skube')}</div></div><span style="font-size:13px;color:${stat[1]};background:${stat[2]};border-radius:999px;padding:3px 12px;flex:none">${E(stat[0])}</span></div>`;
if(D.chips)h+=chips(D.chips);
(D.sections||[]).forEach((s,i)=>{if(s.t==='table')h+=table(s,i);else if(s.t==='tree')h+=tree(s);else if(s.t==='buttons')h+=buttons(s);});
host.innerHTML=h;
</script>
```

Nach dem Widget im Chat-Text nur EIN Satz + ggf. Weiter-Zeile — Karteninhalte NIE als Text doppeln.

## Markdown-Fallback (kein Widget-Tool)

Dieselbe Karte als Markdown (Struktur identisch zur Checkpoint-Karte):

```markdown
## <Emoji> <Job> — <✅ fertig | ⏸️ braucht deine Antwort>

<EIN Klartext-Satz.>

| Was | Ergebnis | Woher |
|---|---|---|
| … | <echter Wert> | <Quelle/Abfrage> |

**Weiter:** „…" = <nächster Schritt>
```

## Sprache (English-first)

Default ist Englisch. Schreibt der User in einer anderen Sprache, sind ALLE sichtbaren Texte
der Karte (Titel, Sektions-Titel, Spaltenköpfe, Button-Labels, `_t`) konsequent in dieser
Sprache — Struktur, Farben und Slash-Befehle bleiben identisch. Checkpoint-Karten:
`render_card.py --lang en|de` eingebaut; jede andere Sprache über `--labels <file.json>`
(die UI-Schlüssel aus `_STRINGS` einmal übersetzen und mitgeben).

## Inhalts-Regeln (gelten für beide Stufen)

- **Vollständigkeit:** Ergebnisse (Befunde, Gruppen, Positionen) IMMER alle ausschreiben — nie
  „+ N weitere". Große ERGEBNIS-Mengen strukturieren (Zwischen-Headings/eigene Tabellen).
- **Input-Echo ≠ Ergebnis:** was der User selbst geliefert hat (Roh-Spalten, Roh-Listen) gehört in
  eine `fold: true`-Sektion — zugeklappt, per Button aufklappbar.
- Jede Zahl mit Herkunft („Woher"). Keine ASCII-Boxen. Kein Roh-JSON im Chat.
- Buttons senden wörtliche Slash-Befehle oder klare Sätze (`sendPrompt`) — der User muss nie raten.
