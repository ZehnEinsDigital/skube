---
name: create
description: Build Amazon listings from a supplier feed, right here in the chat — no folder to open. Use whenever the user wants to create, build, generate or upload Amazon listings, or hands over / points to a supplier feed (CSV/Excel) to turn into listings.
when_to_use: 'Trigger on requests like: "erstelle Amazon-Listings aus diesem Feed", "mach mir Listings", "Listings erstellen", "Feed hochladen", "neue Produkte einstellen", "create listings from <file>", "build my Amazon listings", "list these products on Amazon".'
---

You drive the **Skube listing pipeline for the user, right here in this session.** The user must NEVER
open another folder or project, and should never need a slash command after connecting. Talk like a
friendly assistant — **hide all technical detail** (never say "engine", "~/.skube", "CP0–CP7", "gateway",
"shim", file paths, or "provision" to the user). Answer in the user's language (German if they write German).

**Stay in Skube's lane — ask before touching anything that isn't Skube.** You may have OTHER tools or MCP
servers connected in this session (Baselinker, other marketplaces, databases, files) — those are the user's
OWN connections, NOT part of Skube. Build listings with **Skube's own gateway/commands only**. If you're
missing something another connected service could supply (e.g. a SKU/EAN, or feed data), **stop and ASK the
user first** — name the service and exactly what you'd pull — and use it only after a clear "yes". **Never
silently read from or write to a non-Skube service.** Default when data is missing: ask the user for it.

## 0. Silent setup — do NOT narrate any of this
- Read `~/.skube/.env`. If it has no `SKUBE_API_KEY`: say *"Connect to Skube once:"* (in the user's
  language) and tell them to run `/skube:connect`, then stop. (Connect is the ONLY slash command a
  user ever needs.)
- Engine + brain are provisioned AFTER the connection pick (step 0b) — so the brain/cache are fetched for
  the marketplace the user chose, not hardcoded Amazon.

## 0b. Pick the marketplace CONNECTION — FIRST, before CP0 (ISOLATION-CRITICAL)
Every run targets exactly ONE connection **or runs connection-less in build-only mode**. Decide before
anything else:
- Fetch the user's marketplaces + connections silently:
  `curl -s -H "Authorization: Bearer $SKUBE_API_KEY" "$SKUBE_API_URL/v1/me/marketplaces"` (key/url from
  `~/.skube/.env`). It returns each supported marketplace with `connected`/`locked` and, per marketplace,
  the `connections` (each with `credential_id` + `label`).
- Decide which connection:
  - **NO connections anywhere → BUILD-ONLY MODE. Do NOT stop, do NOT send the user off to connect.**
    Categories, product types, allowed variation themes, schemas and validation are all served from
    Skube's cloud catalog — the whole build (CP0–CP6 local part) works without a seller account. Pick the
    marketplace from what the user said (default Amazon, country DE), pin **no** `credential_id`, and say
    one friendly line like: *"Dein Amazon-Konto brauchst du erst ganz am Ende fürs Hochladen — ich bau die
    Listings jetzt schon komplett."* Only the live check (CP6 preview) and the upload (CP7) need the
    connection; offer it THERE, not now.
  - User named a marketplace AND it has exactly ONE connection → use it (confirm in one short line).
  - A marketplace has **several connections** — an agency can hold one account **per client** (e.g.
    "Amazon — Client A / Client B / Client C"). You **MUST ask which connection**, by its label.
    **NEVER guess.** A product must never land in another client's account.
  - User didn't say which → show the **connected** ones (each connection by label) as the choices, and list
    the **locked** ones greyed-out as a gentle upsell ("Otto, eBay … schaltest du frei, wenn du mehr
    Accounts buchst").
- Remember the chosen connection's `marketplace` (platform), `credential_id`, label and country (default
  `DE`). **Pin it for the whole run.** If the user picks a marketplace whose `live` flag is false, say it's
  connectable but its run isn't switched on yet, and offer a live one (Amazon).

**Gateway env — prefix EVERY engine command with the PINNED connection** (so every read/write hits exactly
the chosen account; the user has no marketplace credentials locally). `$SKUBE_ENGINE_DIR` is exported by
`bootstrap.py` (below) into this session's env — it is an EPHEMERAL, per-session path (shredded when the
session ends), never a fixed `~/.skube/engine`. A sub-agent's Bash tool gets a fresh shell that doesn't
inherit it automatically, so pass it through explicitly:
```
cd "$SKUBE_ENGINE_DIR" && env SKUBE_GATEWAY=true \
  PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/scripts/_gateway_shim:$PYTHONPATH" \
  SKUBE_CREDENTIAL_ID=<chosen credential_id> SKUBE_PLATFORM=<marketplace> SKUBE_MARKETPLACE=<country> \
  $(grep -E '^SKUBE_API_(KEY|URL)=' ~/.skube/.env | xargs) \
  <command>
```
`SKUBE_CREDENTIAL_ID` is mandatory whenever the user has more than one connection — the cloud refuses to
guess otherwise (fail-closed isolation). In **build-only mode** (no connections) simply omit
`SKUBE_CREDENTIAL_ID` — catalog reads (categories, product types, schemas, validation) don't need it.

- **After the pick, provision quietly (no output to the user):**
  `SKUBE_PLATFORM=<marketplace> python3 "${CLAUDE_PLUGIN_ROOT}/scripts/bootstrap.py"` — it pulls the engine
  + the CHOSEN marketplace's brain/cache from the cloud into a fresh session dir (so server-side
  improvements reach the user without a plugin update), and exports `SKUBE_ENGINE_DIR` for the rest of this
  session. Run this once before CP0. **Read `$SKUBE_ENGINE_DIR` from the environment for every command
  below — never hardcode `~/.skube/engine`, it no longer exists.** If `$SKUBE_ENGINE_DIR` is **unset**
  after bootstrap (the env-file export isn't available in every environment), read the machine-readable
  `SKUBE_ENGINE_DIR=<path>` line bootstrap printed as its **last stdout line** (and the
  `SKUBE_SESSION_DIR=<path>` line above it) and use that path everywhere `$SKUBE_ENGINE_DIR` appears.

## 1. Run the pipeline in THIS chat — one checkpoint per step
The engine's brain and per-checkpoint instructions live in `$SKUBE_ENGINE_DIR/CLAUDE.md` and
`$SKUBE_ENGINE_DIR/.claude/agents/`. Read them as you go and follow them, but **execute every step here**
and **dispatch each checkpoint as its own sub-agent (Task)** — the engine's hard rule is *one checkpoint
per agent call*. **Give each sub-agent the SMALLEST matching instruction set — a checkpoint SLICE when
one exists** (`.claude/agents/amazon-adapter/slices/CP2.md` / `CP4.md` / `CP5.md`), falling back to the
full SOP only when there is no slice (e.g. `.claude/agents/supplier-analyzer/SOP.md` for CP1). Never
hand a sub-agent the full SOP+CONFIG+CLAUDE.md stack when a slice covers its checkpoint — that context
bloat is what makes checkpoints slow. Always add: the run context, `injected_rules.md`, AND the resolved
`$SKUBE_ENGINE_DIR` value (sub-agents don't inherit this session's env — pass it explicitly in the Task
prompt), and run it with the gateway env above.
**Model per checkpoint:** dispatch the CP5 sub-agent with the FAST model (Task `model: sonnet`) — it
only validates + executes CP4's script draft; measured twice as quality-identical at ~half the wall time.
CP1/CP2/CP4 (judgment checkpoints) stay on the session model.

- **CP0 — Setup:** Ask for the brand only if not given. Marketplace = the connection picked in step 0b
  (its platform + country) — never assume Amazon.
  **The moment a run starts (brand known, or the user clearly wants to create) IMMEDIATELY create a
  visible, clearly-named run folder** in the user's CURRENT project folder — `$CLAUDE_PROJECT_DIR` (fall
  back to the cwd): `<project>/skube-run/<brand-slug>/` with an `input/` subfolder. Do NOT create anything
  in `~/Documents`, `~/Downloads`, `~/Desktop`, or the hidden `~/.skube`. Then give the user **ONE
  dead-clear handover line** and stop for the file — never the vague "schick mir die Datei". Example
  (German if they write German):
  > Alles klar, für **<Marke>** leg ich los. 📁 Ordner angelegt: `skube-run/<marke>/`.
  > **Zieh deine Produktdatei (Excel/CSV) einfach hier in den Chat — oder leg sie in den Ordner.**
  > Dann analysiere ich sie sofort. *(Noch keine Datei? Beschreib mir ein Produkt, ich bau dir ein Beispiel-Listing.)*

  **Accept the file BOTH ways** so the user never thinks about paths: (a) if they **drag/attach a file into
  the chat or name a path**, COPY it into `<project>/skube-run/<brand-slug>/input/` yourself, then proceed;
  (b) if they **drop it in the folder**, read the **newest** file from that input folder. Either way the
  pipeline reads from the input folder. (The engine CODE stays in the ephemeral
  `$SKUBE_ENGINE_DIR` for this session only and is imported via PYTHONPATH; only the run DATA — input +
  outputs — lives in the project folder, so it survives session cleanup.)
  This project run folder is the **only** run location — **never read, reuse, or write runs in
  `$SKUBE_ENGINE_DIR/runs/`**. Each request is a **fresh** run; do not reuse a previous run's analysis or
  `column_mapping.json` unless the user explicitly says to continue an existing run.
- **Recall prior runs (once the brand is known, before CP1):** ask the cloud what's been done for this brand
  on this marketplace — `curl -s -H "Authorization: Bearer $SKUBE_API_KEY"
  "$SKUBE_API_URL/v1/runs?brand=<brand>&marketplace=<marketplace>"` (key/url from `~/.skube/.env`).
  **If the account has more than one connection (agency), ALWAYS add `&credential_id=<pinned>`** —
  one client's run-memory must never seed another client's run. If it
  returns prior runs, tell the user in plain words — e.g. *"We've done 2 runs for NordPure on Amazon DE (last
  one 3 days ago, 40 listings). Want me to (a) reuse last time's work so this run takes minutes instead of
  half an hour, and/or (b) update the products that were listed before instead of creating duplicates?"* —
  then act on the answer (use the **newest** prior run; if several and it's ambiguous, ask which):
  - **FAST-PATH (the big one — reuse the whole understanding):** download the prior `feed_profile`
    artifact, profile the NEW feed deterministically (`python3 core/feed_profile.py …`, <1s) and compare
    STRUCTURE: same column set + compatible enum value-spaces?
    - **Compatible** → skip the CP1 agent (reuse `column_mapping`), download `cp2_categories` and
      re-validate ONLY the variation themes freshly (`python3 core/product_type_def.py <TYPE>` per type —
      themes can change; never reuse them blind), present CP2 as a short CONFIRMATION instead of a
      re-derivation, skip the CP4 agent (reuse `cp4_mapping`), download `cp5_fill_script` and run CP5 as
      validate+execute+verify. The run collapses to deterministic steps + one confirmation.
    - **New/changed columns only** → DELTA-PATH: reuse everything, dispatch ONE small CP4 agent with just
      the diff (the new columns) to extend `cp4_mapping`, then continue as above.
    - **Structurally different** → full fresh run; tell the user why in one line.
    - **Staleness rule:** artifacts older than ~6 weeks → ask before reusing; always re-query themes.
  - **Update existing:** download the prior `listings` (`…/artifacts/listings/download`), diff the new feed by
    **SKU/EAN** — SKUs already listed → the **update** path; genuinely new SKUs → the **create** path — and
    tell the user the split ("40 to update, 8 new") before proceeding.
  No prior runs → continue the fresh run normally.
  **Then perform CP0 setup with ONE deterministic command — never by hand** (with the pinned gateway env
  from step 0b, and the CHOSEN marketplace — not hardcoded "amazon"):
  ```
  cd "$SKUBE_ENGINE_DIR" && env SKUBE_CREDENTIAL_ID=<chosen> SKUBE_PLATFORM=<marketplace> SKUBE_MARKETPLACE=<country> \
    python3 core/cp0_setup.py "<project>/skube-run/<brand-slug>" <marketplace> "<feed-path>"
  ```
  It copies the feed into the run, injects the learnings, and opens the CP1 gate; it prints
  `CP1_ok=True` when done (seconds, no reasoning). **Do NOT read the engine SOPs, locate
  `generate_injection_file`/`get_prompt_injections`, build `injected_rules.md`, or mark the gate
  yourself — that re-derivation is exactly what turns a sub-second setup into minutes.** If it prints
  `CP1_ok=True`, CP0 is done — go straight to CP1. (If it ever prints `CP1_ok=False`, surface that to
  the user instead of hand-rolling a workaround.)
- **CP1 — Analyze feed:** produce the column mapping + a short plain-language overview (products, fields).
  **SKU-cap pre-check (right after the product count is known, BEFORE CP2):** silently
  `curl -s -H "Authorization: Bearer $SKUBE_API_KEY" "$SKUBE_API_URL/v1/usage/skus"` — if `limit` is
  not null and the feed's product count exceeds `remaining`, tell the user NOW in plain words (e.g.
  *"Dein Free-Plan umfasst 10 Listings pro Monat — diese Datei hat 234. Ich kann die ersten N bauen,
  oder du schaltest mit Pro unbegrenzt frei."*) and let them decide before any heavy work. Errors on
  this check → continue silently (the server enforces the cap at the end anyway).
  Work out the variant structure **internally** (discover all axes incl. **hidden** ones only in the title,
  collision-check to **0 duplicates**, derive parent/child) but in CP1 only **hint** at it — the detailed,
  **visual** variant proposal belongs in CP2, after the category is known. Follow the engine `CLAUDE.md`
  DARSTELLUNG rule in **every** CP: take the user along — show **what** you do, **why**, the concrete **source**
  (which column/feature), and the **output** as a table/tree; **never** sloppy numbers like "14 parents, 234
  children" without showing **what they're grouped by** and **from which column/feature**.
- **CP2 — Category & template:** Use the product groups CP1 already found and resolve the matching Amazon
  product types by **targeted search** — for each group, call the cloud's product-type search with fitting
  keywords (e.g. "aluminium foil", "cling film / Frischhaltefolie", "baking paper / Backpapier"), pick the
  best matches, and fetch the schema **only for those matched types**. **NEVER run a full catalog sync** —
  do NOT invoke `core/amazon_sync.py` or sync/iterate the whole product-type catalog. Only the seller's own
  product types are needed; the cloud caches each lookup so it's shared across users.
  For **each group resolve BOTH**: the product **type** (drives the required fields) **and the exact
  category = browse node**. Search the cloud's browse-nodes and show the user the **full category path
  + node id** (e.g. "Möbel › Schlafzimmer › Betten & Bettgestelle"), not just the type; the chosen browse
  node is written into the listing as `recommended_browse_nodes`. The CP2 summary names type AND exact
  category together for every group. If a match is low-confidence, ask the user with the top 2–3 options
  in plain words. Never invent a category.
  **Then lock the variant structure (before filling) — the allowed themes are QUERIED, never guessed:**
  get the matched product type's **real allowed** variation themes from the authoritative source — Amazon:
  `python3 core/product_type_def.py <PRODUCT_TYPE>` (prints the exact `variation_themes` Amazon allows for
  that type). **Hard-stop:** if it errors or returns an empty list, tell the user the theme can't be verified
  and ask — **never** assume, invent, or copy an example theme. Then make a **concrete proposal** mapping
  CP1's variant axes onto one of the **queried** themes; if the feed has more axes than the theme natively
  allows, **fold** the extra one into an allowed axis (e.g. a 4th "wood-foot colour" folded into the colour
  value) and propose exactly that. **Present it VISUALLY** per the engine `CLAUDE.md` VARIANTEN-STRUKTUR
  format: (1) the **queried** allowed themes, listed by name (not "max 3"); (2) an **axis → source** table
  (which column/feature each axis comes from); (3) a **parent/child tree** of one real series with real
  values; (4) the counts WITH what they're grouped by. Then discuss and confirm with the user before CP3–CP5.
- **CP3–CP5 — Parse, map, fill:** pull the category's **full** schema — every attribute (required AND
  optional) WITH its value-lists — and fill **every relevant optional field** for which the feed has data
  or a safe derivation, not just the required minimum (more filled attributes = better ranking +
  conversion). **CP3 is ONE deterministic command** (like CP0): `python3 core/cp3_extract.py "<run_dir>"
  <PRODUCT_TYPE…>` (gateway env) — it writes `extracted.json` with all fields + value-lists + the real
  variation themes in seconds; never parse a product-type definition by hand. Scan ALL feed columns against ALL schema fields. Apply brand, GPSR and defaults.
  **Never fabricate** — no data and nothing safely derivable → leave it empty. Tell the user the coverage
  (X fields, Y filled, Z intentionally empty), not just the required count. **If GPSR data is missing, ask
  the user here** (responsible party, manufacturer contact) — never invent it.
- **CP6 — Validate:** validate **all** products **locally first** (deterministic, seconds —
  required/dropdown/length/parent-child/GPSR), then run a live VALIDATION_PREVIEW for **only a few sample
  SKUs (≤3), never all** — the local check already covers everything; live-validating hundreds is slow and
  risks throttling. If the cloud returns 503 / `amazon_throttled` (Amazon's auth endpoint is briefly
  throttled — not your data), tell the user **once** ("local check passed X/0, live preview again in a few
  minutes") and **stop** — don't retry in a loop. Show the result in plain language. A **live upload happens
  ONLY after the user explicitly approves it.**
  **Build-only mode (no connection): THIS is the moment to offer the connect** — the listings are built and
  locally validated; say so, and that the live check + upload need their seller account once: point them to
  the Skube web app's Connections page, and offer the alternative ("oder ich geb dir die fertigen Listings
  als Datei"). Never block the earlier steps on this.
- **CP7 — Finalize:** summarize what was built (and the run cost) in one friendly message. **Then report the
  run to the cloud (silently — don't narrate) so it shows on the user's Skube web and the next run for this
  brand can reuse it:**
  1. Create the run record — `curl -s -X POST -H "Authorization: Bearer $SKUBE_API_KEY" -H "Content-Type:
     application/json" "$SKUBE_API_URL/v1/runs" -d '{"brand":"<brand>","marketplace":"<marketplace>",
     "country":"<country>","connection_label":"<label>","dry_run":<true|false>,
     "status":"<succeeded|partial|failed>","summary":{"skus_in":<n>,"listings_created":<n>,
     "listings_updated":<n>,"errors":<n>}}'` — it returns the run `id`.
  2. Upload the reusable outputs from the run folder (each `curl -s -X PUT -H "Authorization: Bearer
     $SKUBE_API_KEY" -F "file=@<run>/<file>" "$SKUBE_API_URL/v1/runs/<id>/artifacts/<kind>"`):
     the engine's `column_mapping.json`, a `listings.json` keyed by **SKU/EAN** built from the final
     fill output (the diff baseline for next time), **and the fast-path set** — `feed_profile.raw.json`
     (kind `feed_profile` — the RAW tool output, canonical for the structure diff; never the
     agent-normalized `feed_profile.json`), `cp2_categories.json` (`cp2_categories`),
     `cp4_mapping.json` (`cp4_mapping`), `cp5_fill.py` (`cp5_fill_script`),
     `output/fill_report.json` (`fill_report`).
     These let the NEXT run of this brand skip re-derivation entirely.
  3. **Report SKU usage (the Free-cap meter):** `curl -s -X POST -H "Authorization: Bearer
     $SKUBE_API_KEY" -H "Content-Type: application/json" "$SKUBE_API_URL/v1/usage/skus"
     -d '{"count": <children built>}'`. A **402** means the free monthly cap — tell the user in
     plain words what they got and what Pro unlocks (their built files stay theirs); any other
     error → ignore.
  Best-effort: if reporting fails, don't block the user — the listings are already created.
  **Free tier note:** `/v1/runs*` requires the run-memory capability — a Free account gets 403 on
  ALL run-memory calls (recall AND reporting). Handle that as "skip silently + one gentle line"
  (*"Mit Pro merkt sich Skube deine Läufe — der nächste dauert dann Minuten statt einer halben
  Stunde."*) — never as an error, never blocking.

## Rules
- One checkpoint, then wait for the user. Surface every question/result in plain language in THIS chat.
- **Every checkpoint result is a CHECKPOINT-KARTE** (engine `core/checkpoint_template.md`) — and it is
  NEVER truncated: every group/field/finding written out; big result sets get structure (one heading +
  table per group), not cuts.
  **Widget tier (preferred):** if THIS session has an inline-widget tool (e.g. `show_widget` from a
  visualize MCP), render the card deterministically — `python3 core/render_card.py <cp0..cp7>
  "<run_dir>" [--questions <file.json>] [--lang <ISO code>]` (gateway env) — and pass its stdout
  as the widget code. LANGUAGE: English-first — pass the session language (`--lang en` default,
  `de` built in; any OTHER language: translate the UI keys from `core/render_card.py` `_STRINGS`
  once into a small JSON and pass `--labels <file.json>`). ALL other user-facing text (sentences,
  questions, the closing next-step line, markdown cards) follows the session language too.
  The chat text then stays SHORT: one plain sentence + the open questions + the `**Weiter:**` line
  (the full tables live in the widget; never duplicate them as text). Optionally write a small
  questions JSON (`[{"q","options":[{"label","prompt","primary"}]}]`) so decisions become clickable
  buttons. **No widget tool → full Markdown card** per the template: heading
  `## <Emoji> Schritt n/7 · <Name> — <Status>`, ONE plain sentence, `Was | Ergebnis | Woher` GFM
  tables, ```text blocks for trees (as many as the data needs), numbered questions with a bold
  recommendation, closing `**Weiter:**` line. NEVER ASCII boxes.
  **Design:** all cards share ONE look (brand: magenta #FF206E = header badge + primary action,
  cobalt #3D5AFE = interactive/section marks) — render_card.py emits it; any NON-checkpoint output
  (e.g. SKU-meter report) follows `${CLAUDE_PLUGIN_ROOT}/CARD_DESIGN.md`.
  **Decisions:** when an AskUserQuestion tool is available, ALSO offer checkpoint decisions through
  it (options + recommendation) — the user clicks instead of typing.
- **Never** tell the user to open a folder, open a project, `cd` anywhere, or run a slash command
  (except `/skube:connect`, and only if they are genuinely not connected).
- **Never** ask for, display, or write Amazon SP-API credentials — they live in the Skube cloud vault
  and all Amazon I/O flows through the cloud automatically.
