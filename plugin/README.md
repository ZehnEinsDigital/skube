# Skube — your Amazon listing copilot for Claude Code

Skube turns supplier feeds into upload-ready Amazon listings and helps you check, update, and fix
existing listings — **inside your own Claude Code**. The AI reasoning runs on **your** Claude plan;
your **Amazon credentials and the actual uploads stay in the Skube cloud** and never touch your
machine. Flat monthly subscription — no per-token bill from us.

## Before you start

1. **Claude Code on a paid Claude plan.** That means the **Code** tab of the Claude Desktop app, the
   Claude Code CLI, or an IDE extension. (The Desktop **Chat** tab, custom connectors, and ChatGPT
   can't run it — Skube needs Bash + sub-agents.)
2. **A Skube account** with an active subscription — sign up at the Skube web app. A fresh signup is
   active right away during the test phase.

## Setup — 3 steps

**1 · Install the plugin** (no terminal needed)
In Claude Code: **+** menu → **Plugins** → **Add marketplace** → **Add from a repository** → paste
`ZehnEinsDigital/skube` → install **skube**. Or by command:
```
/plugin marketplace add ZehnEinsDigital/skube
/plugin install skube@skube
```

**2 · Connect your account** (one click — nothing to paste)
In Claude Code run:
```
/skube:connect
```
It opens your browser to the Skube web app — log in if needed, click **Authorize**, done. The key is
delivered to your machine and saved to `~/.skube/.env` automatically; you never copy or paste it.
(Advanced/CLI: set `SKUBE_API_KEY` in `~/.skube/.env` yourself.) Never enter Amazon or Anthropic keys.

**3 · Use it**
```
/skube:create ./my-supplier-feed.csv
```
The engine downloads itself on first run (into an ephemeral per-session dir under `~/.skube/.sessions/`,
cleaned up when the session ends), pulls the current Skube "brain", and walks you through the listing
step by step, pausing whenever it needs a decision from you.

> Amazon credentials live only in the Skube web app's encrypted vault — store them there once.

## Commands

You mostly **just talk to it** — e.g. *"erstelle Listings aus dieser Datei"* or *"wie viel hab ich verkauft?"*.
The slash commands are there if you prefer them:

| Command | What it does |
|---------|--------------|
| `/skube:connect` | One-time: connect your Skube account (browser, nothing to paste) |
| `/skube:create <feed> [brand]` | Build Amazon listings from a supplier feed |
| `/skube:status <sku>` | What Amazon reports about a listing right now |
| `/skube:sales [--days N]` | Your real Amazon sales — units, revenue, sessions (PII-free) |
| `/skube:diagnose <sku>` | Explain a rejection/suppression + propose a fix |
| `/skube:update <skus> <change>` | Partial content update (keeps ASIN/reviews) |

## How it works (and why it's safe)

- The reasoning + the deterministic engine run **locally on your plan** — we never see your tokens.
- Each run pulls the current **brain** (learnings + marketplace rules) from Skube, **gated by your
  subscription**. No active plan → no fresh brain, no upload.
- Every Amazon read/write goes through the **Skube cloud gateway**, which holds your credentials and
  performs the call server-side. The plugin can **never** write to a marketplace directly — uploads are
  subscription-gated and dry-run by default until you approve.
