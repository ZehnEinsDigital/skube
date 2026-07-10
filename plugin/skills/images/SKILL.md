---
name: images
description: Product-image creation for listings — a copy-paste-ready prompt series (hero, lifestyle, detail …) built from the listing's own data, respecting each marketplace's image rules; hosted URLs then apply as a gated media update. Use whenever the user wants new or better product images.
when_to_use: 'Trigger on: "neue Produktbilder", "besseres Hauptbild", "Bilder für mein Listing", "Hero-Bild", "product images", "new hero image", "image prompts", "bessere Bilder".'
---

Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bootstrap.py"` quietly (auth). Then fetch THIS job's
**current playbook from Skube's server and follow it EXACTLY** — the workflow lives server-side, so it stays
up to date with no plugin release:

```bash
source ~/.skube/.env 2>/dev/null
curl -s -H "Authorization: Bearer $SKUBE_API_KEY" \
  "${SKUBE_API_URL:-https://skube-api-production.up.railway.app}/v1/skills/update"
```

Follow the returned playbook's **"IMAGE CREATION"** section (prompt series from Skube's own listing
data — never scraping; marketplace image rules baked in; the user's hosted URLs then apply as a normal
gated media update). The returned Markdown is the authoritative, always-current instructions — do
exactly what it says (it may reference `${CLAUDE_PLUGIN_ROOT}/scripts/*` helpers, which this plugin
provides). If the response is empty or errors, the Skube connection isn't reachable here — tell the
user to run `/skube:connect`, then stop. **This skill is a thin shell; the logic is on the server.**
