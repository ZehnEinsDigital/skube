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
let h=`<div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap"><div style="width:40px;height:40px;border-radius:10px;background:${B1};display:flex;align-items:center;justify-content:center;flex:none"><i class="ti ti-${D.head.icon||'cube'}" style="font-size:22px;color:#fff" aria-hidden="true"></i></div><div style="flex:1;min-width:180px"><div style="font-size:18px;font-weight:500;color:var(--text-primary)">${E(D.head.title)}</div><div style="font-size:12.5px;color:var(--text-secondary)">${E(D.head.step?T.step+' '+D.head.step:D.head.job||'skube')}</div></div><span style="font-size:13px;color:${stat[1]};background:${stat[2]};border-radius:999px;padding:3px 12px;flex:none">${E(stat[0])}</span></div>`;
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
