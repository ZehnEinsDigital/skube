# Skube card design — ONE look for ALL outputs

Every result shown to the user (status, diagnose, update, sales — and the create flow's checkpoints)
is a **Skube card**: plain **GitHub Markdown**, never a widget. A `show_widget` render costs a
`read_me` + `show_widget` round-trip and leaves a large HTML blob in context for the whole session;
Markdown renders instantly and reads identically. `served-engine/core/render_card.py` is the SSOT
(checkpoint cards, CP0–CP7); `scripts/card.py` is the plugin twin (job cards) — its `to_markdown` is
kept **byte-identical** to `render_card.py` (a test in `api/tests/test_card.py` asserts it). This doc
is the data-structure contract both share.

## How to render — Markdown, never a widget

Build ONLY the data structure `D` (below), write it as a JSON file, and render deterministically:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/card.py" <d.json>     # stdout = the finished Markdown card
```

**Print that stdout straight into the chat.** 🔴 Do NOT call `show_widget`, do NOT call `read_me`, do
NOT build any HTML. You may add ONE plain-language sentence of context before the card — never
duplicate the card's tables as prose.

## The data structure `D`

```js
D = {
  head: { emoji: "📊", job: "Sales", title: "Amazon DE · 30 days", status: "done" },
        // emoji = the card's leading emoji; job = the card kind (Sales/Status/Diagnosis/Update).
        // status: "done" | "ask". The create flow uses step:"1/7" instead of job.
  chips: [ { v: "1,204", l: "Units" }, { v: "€89,312", l: "Revenue" } ],  // key figures → one stat line
  _t: { step: "Step", ask: "⏸️ needs your answer", done: "✅ done" },  // status labels in session language; omit = English
  sections: [
    { t: "table", title: "…", cols: ["What","Result","Source"], rows: [[…]] },  // GFM table, ALL rows
    { t: "table", title: "Show all N …", fold: true, cols: […], rows: [[…]] },   // input echo → collapsed hint
    { t: "tree",  title: "…", text: "Series …\n ├─ …" },                          // fenced ```text block
    { t: "buttons", title: "To clarify", items: [ { label: "…", primary: true } ] }  // → numbered options
  ]
}
```

## The rendered card (what `card.py` prints)

```markdown
## 📊 Sales · Amazon DE · 30 days — ✅ done

**1,204** Units · **€89,312** Revenue

### What | Result | Source
| What | Result | Source |
|---|---|---|
| … | <real value> | <source/query> |

**Next:** "ok" = continue
```

- `head` → `## <emoji> <job|Step n> · <title> — <status>`
- `chips` → one compact **bold** stat line
- `table` → GFM table (every row; a `fold` table collapses to a one-line "say 'columns'" hint)
- `tree` → fenced ```text block (real values)
- `buttons` → a `**To clarify:**` numbered list (recommended option **bold**) + the `**Next:**` line

## Language (English-first)

Default English. If the user writes in another language, ALL visible texts (title, section titles,
column headers, button labels, `_t`) are consistently in that language — structure and `/skube:*`
commands stay identical. Checkpoint cards: `render_card.py --lang en|de` (built in) or
`--labels <file.json>` for any other language (translate the UI keys from `_STRINGS` once).

## Content rules

- **Completeness:** ALWAYS write out all results (findings, groups, items) — never "+ N more".
  Structure large result sets (sub-headings / own tables), never truncate.
- **Input echo ≠ result:** what the user supplied (raw columns/lists) goes in a `fold: true` section.
- Every number with its origin ("Source"). No ASCII boxes. No raw JSON in the chat.
