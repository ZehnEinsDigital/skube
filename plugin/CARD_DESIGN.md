# Skube card design — ONE look for ALL job outputs

Every result output to the user (status, diagnose, update, sales — and everything future) is a
**Skube card** in exactly this design. The create flow's checkpoint cards are rendered
deterministically by `core/render_card.py` — this document is the **mirror** of the same design for
cards whose content the agent assembles itself. If the design changes: `render_card.py`
is the SSOT, this file follows.

## Brand colors (fixed)

| Role | Color | Use |
|---|---|---|
| Primary color | `#FF206E` (magenta) | Header badge (job/step), primary action buttons |
| Secondary color | `#3D5AFE` (cobalt) | Section dot, secondary buttons, fold-open buttons, icons, links |
| Status | green `#1a6b3c`/`#e3f2e8` · amber `#8a5a00`/`#fdf0d5` | ONLY state (done / needs answer) — never for decoration |

Rules: magenta = "this is the action / this is Skube". Cobalt = "this is clickable/interactive".
Status stays semantic. Everything else host variables (`var(--text-primary)` etc.) — never hardcoded gray.

## Widget tier (session has an inline-widget tool)

**🔴 HOW TO DISPLAY IT — this is the step that was missing. If a `show_widget` tool exists in the session
(e.g. `mcp__visualize__show_widget` — the Claude Desktop app HAS it), you MUST render the card as a widget.
Do it by CALLING the tool, not by printing HTML:**
1. **Once per session, before your first widget:** call the visualize `read_me` tool (its required setup).
2. Build `D` → `card.py` → the finished widget code (below).
3. **Call `show_widget`** with that code as the `widget_code` argument. **NEVER paste the `<div>`/`<script>`
   into the chat as text** — printed HTML does NOT render; that is exactly why users saw a plain table.
Only when NO `show_widget`/inline-widget tool exists in the session → the Markdown fallback below.

Card = `<div id="sk-card">` + `<script>` with a data structure `D` + the standard JS below.
The agent builds ONLY `D` — the layout comes from the JS, so every card looks identical.

**Recommended path — don't retype:** write `D` as a JSON file and render deterministically:
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/card.py" <d.json>` → stdout is the finished widget code
(the script reads the standard JS below from this file; the release build mirrors it
automatically from `render_card.py`). Only copy the JS below 1:1 when Python is not
available in the session.

```js
D = {
  head: { icon: "chart-bar", emoji: "📊", job: "Sales", title: "Amazon DE · 30 days", status: "done" },
        // icon = Tabler outline name (magenta tile); status: "done" | "ask";
        // the create flow uses step:"1/7" instead of job. emoji only for the Markdown fallback.
  chips: [ { v: "1,204", l: "Units" }, { v: "€89,312", l: "Revenue" } ],   // key figures
  _t: { step: "Step", ask: "⏸️ needs your answer", done: "✅ done" },  // status labels — set in the session language; omit = English
  sections: [
    { t: "table", title: "…", cols: ["What","Result","Source"], rows: [[…]] },
    { t: "table", title: "Show all N …", fold: true, cols: […], rows: [[…]] },  // input echo/long tail
    { t: "tree",  title: "…", text: "Series …\n ├─ …" },
    { t: "buttons", title: "To clarify", note: "…", items: [
        { label: "…", prompt: "…", primary: true } ] }        // primary = magenta, otherwise cobalt
  ]
}
```

Standard JS (mirror of `render_card.py` — copy 1:1, do not restructure):

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
const SKM='<svg viewBox="0 0 200 200" width="34" height="34" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="skm" gradientUnits="userSpaceOnUse" x1="22" y1="22" x2="182" y2="182"><stop offset="0" stop-color="#ff206e"/><stop offset="1" stop-color="#3d5afe"/></linearGradient></defs><path fill="url(#skm)" fill-rule="evenodd" clip-rule="evenodd" d="M100 4.08718e-06L200 0V4.7619C200 17.8941 197.413 30.8977 192.388 43.0303C187.363 55.1628 179.997 66.1867 170.711 75.4726C161.425 84.7584 150.401 92.1244 138.268 97.1499C127.571 101.581 116.196 104.116 104.654 104.654C104.116 116.196 101.581 127.571 97.1499 138.268C92.1244 150.401 84.7584 161.425 75.4726 170.711C66.1867 179.997 55.1628 187.363 43.0303 192.388C30.8977 197.413 17.8941 200 4.7619 200H0V100C-4.54131e-07 86.8678 2.58658 73.8642 7.61205 61.7317C12.6375 49.5991 20.0035 38.5752 29.2893 29.2893C38.5752 20.0035 49.5991 12.6375 61.7317 7.61205C73.8642 2.58658 86.8678 4.08718e-06 100 4.08718e-06ZM104.762 95.1127C115.016 94.5723 125.116 92.2894 134.624 88.351C145.601 83.8041 155.575 77.1397 163.976 68.7382C172.378 60.3367 179.042 50.3627 183.589 39.3856C187.528 29.8775 189.81 19.778 190.351 9.52381L104.762 9.52381V95.1127ZM95.2381 9.64921V95.2381H9.64921C10.1896 84.9839 12.4725 74.8844 16.4109 65.3763C20.9578 54.3992 27.6222 44.4252 36.0237 36.0237C44.4252 27.6222 54.3992 20.9578 65.3763 16.4109C74.8844 12.4725 84.9839 10.1896 95.2381 9.64921ZM9.52381 104.762H95.1127C94.5723 115.016 92.2894 125.116 88.351 134.624C83.8041 145.601 77.1397 155.575 68.7382 163.976C60.3367 172.378 50.3627 179.042 39.3856 183.589C29.8775 187.528 19.778 189.81 9.52381 190.351V104.762ZM159.524 128.571C155.459 128.571 151.434 129.372 147.679 130.928C143.924 132.483 140.511 134.763 137.637 137.637C134.763 140.511 132.483 143.924 130.928 147.679C129.372 151.434 128.571 155.459 128.571 159.524C128.571 163.589 129.372 167.613 130.928 171.369C132.483 175.124 134.763 178.536 137.637 181.41C140.511 184.285 143.924 186.565 147.679 188.12C151.434 189.676 155.459 190.476 159.524 190.476C163.589 190.476 167.613 189.676 171.369 188.12C175.124 186.565 178.536 184.285 181.41 181.41C184.285 178.536 186.565 175.124 188.12 171.369C189.676 167.613 190.476 163.589 190.476 159.524C190.476 155.459 189.676 151.434 188.12 147.679C186.565 143.924 184.285 140.511 181.41 137.637C178.536 134.763 175.124 132.483 171.369 130.928C167.613 129.372 163.589 128.571 159.524 128.571ZM144.034 122.129C148.945 120.095 154.208 119.048 159.524 119.048C164.839 119.048 170.103 120.095 175.013 122.129C179.924 124.163 184.386 127.144 188.145 130.903C191.903 134.661 194.885 139.123 196.919 144.034C198.953 148.945 200 154.208 200 159.524C200 164.839 198.953 170.103 196.919 175.013C194.885 179.924 191.903 184.386 188.145 188.145C184.386 191.903 179.924 194.885 175.013 196.919C170.103 198.953 164.839 200 159.524 200C154.208 200 148.945 198.953 144.034 196.919C139.123 194.885 134.661 191.903 130.903 188.145C127.144 184.386 124.163 179.924 122.129 175.013C120.095 170.103 119.048 164.839 119.048 159.524C119.048 154.208 120.095 148.945 122.129 144.034C124.163 139.123 127.144 134.661 130.903 130.903C134.661 127.144 139.123 124.163 144.034 122.129Z"/></svg>';
const _brand=(!D.head.icon||D.head.icon=='cube'||D.head.icon=='skube');
const _tile=_brand?'<div style="width:40px;height:40px;display:flex;align-items:center;justify-content:center;flex:none">'+SKM+'</div>':`<div style="width:40px;height:40px;border-radius:10px;background:${B1};display:flex;align-items:center;justify-content:center;flex:none"><i class="ti ti-${D.head.icon}" style="font-size:22px;color:#fff" aria-hidden="true"></i></div>`;
let h=`<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap">${_tile}<div style="flex:1;min-width:180px"><div style="font-size:18px;font-weight:500;color:var(--text-primary)">${E(D.head.title)}</div><div style="font-size:12.5px;color:var(--text-secondary)">${E(D.head.step?T.step+' '+D.head.step:D.head.job||'skube')}</div></div><span style="font-size:13px;color:${stat[1]};background:${stat[2]};border-radius:999px;padding:3px 12px;flex:none">${E(stat[0])}</span></div>`;
if(D.chips)h+=chips(D.chips);
(D.sections||[]).forEach((s,i)=>{if(s.t==='table')h+=table(s,i);else if(s.t==='tree')h+=tree(s);else if(s.t==='buttons')h+=buttons(s);});
host.innerHTML=h;
</script>
```

After the widget, the chat text is ONE sentence + a next-step line if needed — NEVER duplicate card contents as text.

## Markdown fallback (no widget tool)

The same card as Markdown (structure identical to the checkpoint card):

```markdown
## <Emoji> <Job> — <✅ done | ⏸️ needs your answer>

<ONE plain-language sentence.>

| What | Result | Source |
|---|---|---|
| … | <real value> | <source/query> |

**Next:** "…" = <next step>
```

## Language (English-first)

Default is English. If the user writes in another language, ALL visible texts of the
card (title, section titles, column headers, button labels, `_t`) are consistently in that
language — structure, colors and slash commands stay identical. Checkpoint cards:
`render_card.py --lang en|de` built in; any other language via `--labels <file.json>`
(translate the UI keys from `_STRINGS` once and pass them along).

## Content rules (apply to both tiers)

- **Completeness:** ALWAYS write out all results (findings, groups, items) — never
  "+ N more". Structure large RESULT sets (sub-headings/own tables).
- **Input echo ≠ result:** what the user supplied themselves (raw columns, raw lists) belongs in
  a `fold: true` section — collapsed, expandable via button.
- Every number with its origin ("Source"). No ASCII boxes. No raw JSON in the chat.
- Buttons send literal slash commands or clear sentences (`sendPrompt`) — the user never has to guess.
