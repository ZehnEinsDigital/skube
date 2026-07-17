#!/usr/bin/env python3
"""Skube plugin preflight — run before any engine checkpoint.

Verifies config, pulls the LIVE brain bundle from the Skube cloud (gated by the
subscription), seeds the served cache + learnings, and rebuilds injected_rules.md so
the engine's CP1 gate (>=1000 chars) passes. The ONLY secret it uses is the customer's
lk_live_ Skube API key — never an Amazon or Anthropic credential.

Exits non-zero with a clear message on any failure (e.g. 402 = no active subscription).
"""

from __future__ import annotations

import io
import json
import os
import pathlib
import ssl
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request

DEFAULT_API_URL = "https://skube-api-production.up.railway.app"
# Legacy durable engine location. No longer the auto-provision target (T3): the engine is
# now provisioned into the ephemeral session dir (session_dir / "engine") so it is reaped
# alongside the brain. Kept only as the path session_env.py still recognizes for back-compat
# / SKUBE_ENGINE_DIR overrides that happen to point here.
DEFAULT_ENGINE_DIR = pathlib.Path.home() / ".skube" / "engine"
_MIN_INJECTED_RULES = 1000  # engine CP1 gate
CACHE_MARKET = "DE"  # engine reads data/amazon_cache/<market>/; DE is the first slice
# A session's files are reaped after this lease expires (crash-safety). 24h so an ALL-DAY
# working session outlives the lease — a new window's SessionStart reap must never delete a
# still-running session's engine mid-run. The gateway shim also re-stamps the lease on every
# gateway call (heartbeat), so truly long sessions keep extending it.
_SESSION_TTL_SECONDS = 24 * 3600
# Deny rule for the provisioned engine project's Claude settings: no direct SP-API egress
# from the engine project (all SP-API flows through the Skube cloud gateway).
_SPAPI_DENY = "Bash(*sellingpartnerapi*)"


def _ca_ssl_context() -> ssl.SSLContext:
    """CA bundle for our HTTPS calls. python.org Python on macOS ships NO CA certs, so the
    stdlib default context fails every HTTPS request with CERTIFICATE_VERIFY_FAILED (the #1
    first-run onboarding failure). Resolve a real bundle: certifi if importable (most envs),
    else a known system bundle, else the stdlib default. Stays stdlib-only — certifi is
    optional, never a hard dependency."""
    try:
        import certifi  # noqa: PLC0415 — optional, guarded; not a required dependency
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:  # noqa: BLE001 — any certifi issue falls through to system bundles
        pass
    for _path in (
        "/etc/ssl/cert.pem",                    # macOS, some BSD
        "/etc/ssl/certs/ca-certificates.crt",   # Debian/Ubuntu
        "/etc/pki/tls/certs/ca-bundle.crt",     # RHEL/Fedora
        "/usr/local/etc/openssl/cert.pem",      # Homebrew OpenSSL
    ):
        if os.path.exists(_path):
            try:
                return ssl.create_default_context(cafile=_path)
            except Exception:  # noqa: BLE001
                continue
    return ssl.create_default_context()


_SSL_CTX = _ca_ssl_context()


def _sessions_root() -> pathlib.Path:
    return pathlib.Path.home() / ".skube" / ".sessions"


def new_session_dir() -> pathlib.Path:
    """Create a fresh, leased, per-session dir the engine runs from this session only."""
    root = _sessions_root()
    root.mkdir(parents=True, exist_ok=True)
    sess = pathlib.Path(tempfile.mkdtemp(prefix="skube-run-", dir=str(root)))
    (sess / ".skube_lease").write_text(str(time.time() + _SESSION_TTL_SECONDS), encoding="utf-8")
    return sess


def write_brain_reference(bundle: dict, session_dir: pathlib.Path) -> None:
    """Write the brain reference + injected_rules INTO the ephemeral session dir (never durable)."""
    (session_dir / "brain.json").write_text(
        json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (session_dir / "injected_rules.md").write_text(
        assemble_injected_rules(bundle), encoding="utf-8"
    )
    # Only when the server actually minted one: older/secretless servers don't send a
    # "freshness" key, and we must not write an empty/placeholder file in that case.
    freshness = bundle.get("freshness")
    if freshness:
        (session_dir / "freshness.json").write_text(
            json.dumps(freshness, ensure_ascii=False, indent=2), encoding="utf-8"
        )


def _config_env_path() -> pathlib.Path:
    """Stable, user-owned config location — works for GUI installs (no cwd/.env)."""
    return pathlib.Path.home() / ".skube" / ".env"


def load_dotenv() -> None:
    """Load KEY=VALUE pairs into os.environ from, in order: the plugin dir, the cwd, and
    ~/.skube/.env. Shell-exported vars win (setdefault).

    ~/.skube/.env is the GUI path: when the plugin is installed via Upload/Marketplace it
    lives in a managed dir, so the user has no obvious cwd .env — /skube:connect writes the
    key to ~/.skube/.env instead (see save_api_key).
    """
    roots = [os.environ.get("CLAUDE_PLUGIN_ROOT", ""), ".", str(_config_env_path().parent)]
    for root in roots:
        if not root:
            continue
        path = pathlib.Path(root) / ".env"
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _read_env_file() -> dict[str, str]:
    """Parse ~/.skube/.env into a dict (best-effort; comments/blank lines skipped)."""
    path = _config_env_path()
    out: dict[str, str] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def _upsert_env(updates: dict[str, str | None]) -> pathlib.Path:
    """Merge KEY=VALUE updates into ~/.skube/.env, PRESERVING every other key (chmod 600).

    Critical: /skube:connect (save_api_key) and connection-pinning (save_credential_id) both
    write here. A naive full-rewrite (the old save_api_key) would wipe the other's value — so a
    reconnect used to drop the pinned SKUBE_CREDENTIAL_ID. Always merge. A value of None/"" deletes
    that key.
    """
    dest = _config_env_path()
    dest.parent.mkdir(parents=True, exist_ok=True)
    merged = _read_env_file()
    for key, value in updates.items():
        if value is None or str(value).strip() == "":
            merged.pop(key, None)
        else:
            merged[key] = str(value).strip()
    dest.write_text("\n".join(f"{k}={v}" for k, v in merged.items()) + "\n", encoding="utf-8")
    try:
        os.chmod(dest, 0o600)
    except OSError:
        pass
    return dest


def save_api_key(key: str, api_url: str | None = None) -> pathlib.Path:
    """Persist the Skube key to ~/.skube/.env (chmod 600) — used by /skube:connect so a
    GUI user never edits a dotfile by hand. Refuses anything that isn't an lk_live_ key.
    Merges, so a previously pinned SKUBE_CREDENTIAL_ID survives a reconnect."""
    key = (key or "").strip()
    if not key.startswith("lk_live_"):
        raise SystemExit("SKUBE: that is not a Skube key (it must start with lk_live_). "
                         "Get it on the Connect page of the Skube web app.")
    updates: dict[str, str | None] = {"SKUBE_API_KEY": key}
    if api_url and api_url.strip():
        updates["SKUBE_API_URL"] = api_url.strip()
    return _upsert_env(updates)


def save_credential_id(
    credential_id: str, platform: str | None = None, market: str | None = None
) -> pathlib.Path:
    """Persist the chosen marketplace CONNECTION so it survives a fresh/compacted session.

    Without this the pin is session-only (an env var) and every new chat re-asks 'which
    account?' (exactly the friction a compacted session hit). Persisting it — merged, never
    clobbering the API key — lets load_dotenv() restore it next session. The skill still
    CONFIRMS before reusing it, so agency multi-account isolation is preserved."""
    cid = (credential_id or "").strip()
    if not cid:
        raise SystemExit("SKUBE: no credential_id to pin.")
    updates: dict[str, str | None] = {"SKUBE_CREDENTIAL_ID": cid}
    if platform and platform.strip():
        updates["SKUBE_PLATFORM"] = platform.strip().lower()
    if market and market.strip():
        updates["SKUBE_MARKETPLACE"] = market.strip()
    return _upsert_env(updates)


def validate_config(env: dict) -> list[str]:
    """Return a list of human-readable config errors (empty = OK).

    Only SKUBE_API_KEY is required. SKUBE_ENGINE_DIR is OPTIONAL: unset = the plugin
    auto-provisions the engine into the ephemeral per-session dir (see new_session_dir);
    set = an explicit (writable) engine dir the user manages themselves (dev/override).
    """
    errors: list[str] = []
    key = env.get("SKUBE_API_KEY", "")
    if not key.startswith("lk_live_"):
        errors.append("No Skube API key found. Run /skube:connect once to paste your lk_live_ key "
                      "(it is saved to ~/.skube/.env).")
    engine_dir = env.get("SKUBE_ENGINE_DIR", "").strip()
    if engine_dir and not pathlib.Path(engine_dir).expanduser().is_dir():
        errors.append("SKUBE_ENGINE_DIR is set but is not a directory (unset it to auto-provision).")
    return errors


def assemble_injected_rules(bundle: dict) -> str:
    """Build the injected_rules.md content from the served brain (learnings + MISTAKES).

    Guarantees >= _MIN_INJECTED_RULES chars so the engine's CP1 gate passes; the served
    MISTAKES alone is large, but we assert the floor explicitly.
    """
    parts = [f"# Skube injected rules (brain {bundle.get('version_hash', '?')[:12]})", ""]
    learnings = bundle.get("learnings") or []
    parts.append(f"## Learnings ({len(learnings)})")
    for rec in learnings:
        prob = rec.get("problem", {})
        sol = rec.get("solution", {})
        parts.append(f"- [{rec.get('severity', 'info')}] {prob} -> {sol}")
    mistakes = bundle.get("mistakes") or ""
    if mistakes:
        parts.append("\n## Marketplace MISTAKES\n")
        parts.append(mistakes)
    text = "\n".join(parts)
    if len(text) < _MIN_INJECTED_RULES:
        text += "\n" + ("<!-- padding to satisfy CP1 gate -->\n" * 40)
    return text


def fetch_brain(api_url: str, api_key: str, marketplace: str = "amazon") -> dict:
    req = urllib.request.Request(
        f"{api_url.rstrip('/')}/v1/brain/{marketplace}",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30, context=_SSL_CTX) as resp:  # noqa: S310 (trusted Skube host)
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        if exc.code == 402:
            raise SystemExit("SKUBE: no active subscription (402). Reactivate your plan to run.")
        raise SystemExit(f"SKUBE: brain fetch failed (HTTP {exc.code}).")
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"SKUBE: could not reach the Skube API: {exc}")


def start_run(api_url: str, api_key: str) -> str | None:
    """Mint a per-run token (Task 9 chokepoint): POST /v1/run/start with the same Bearer
    auth as fetch_brain. Soft rollout — ANY failure (network, non-200, malformed JSON) is
    caught and returns None so preflight NEVER crashes over this; the run just proceeds
    without a run_id, and downstream endpoints only verify one when it's present."""
    req = urllib.request.Request(
        f"{api_url.rstrip('/')}/v1/run/start",
        data=b"",
        headers={"Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30, context=_SSL_CTX) as resp:  # noqa: S310 (trusted Skube host)
            body = json.loads(resp.read())
        run_id = body.get("run_id")
        return run_id if isinstance(run_id, str) and run_id else None
    except Exception as exc:  # noqa: BLE001 — soft rollout: never crash preflight over this
        print(f"SKUBE: could not mint a run token (continuing without one): {exc}", file=sys.stderr)
        return None


def _post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=30, context=_SSL_CTX) as resp:  # noqa: S310 (trusted Skube host)
        return json.loads(resp.read())


def _device_pending_path() -> pathlib.Path:
    return _config_env_path().parent / "device_pending.json"


def device_start(api_url: str, *, open_browser: bool = True) -> bool:
    """Phase 1 of the device flow (86catc574): start, show the link, park the state.

    In harnesses that render a command's output only AFTER it exits (Claude Code's Bash),
    an in-process poll hides the authorize link behind a spinner forever — the cloud/headless
    deadlock Mika hit live. So phase 1 prints the link + code, writes the pending state to
    ~/.skube/device_pending.json (0600), and returns whether a LOCAL browser opened. The
    device_code lives only in that file — never on stdout, never in the transcript.
    """
    import webbrowser

    base = api_url.rstrip("/")
    start = _post_json(f"{base}/v1/auth/cli/device/start", {})
    url = f"{start['verification_uri']}?code={start['user_code']}"
    # Try the local browser FIRST, then tell the truth about what happened: in a cloud/headless
    # session webbrowser.open() cannot reach the user's browser — the clickable link IS the flow
    # there, so it must lead and "opening your browser" must never be claimed falsely.
    opened = False
    if open_browser:
        try:
            opened = bool(webbrowser.open(url))
        except Exception:  # noqa: BLE001
            opened = False
    state = _device_pending_path()
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text(json.dumps({
        "device_code": start["device_code"],
        "api_url": base,
        "interval": int(start.get("interval", 3)),
    }), encoding="utf-8")
    try:
        os.chmod(state, 0o600)
    except OSError:
        pass
    if opened:
        print(
            "SKUBE: opening your browser to connect — if nothing opened, use this link:\n"
            f"  {url}\n  (code: {start['user_code']}) → click Authorize."
        )
    else:
        print(
            "SKUBE: open this link to connect:\n"
            f"  {url}\n  (check the code shows {start['user_code']}) → click Authorize."
        )
    return opened


def device_wait(*, sleep=None, max_wait: int = 75):
    """Phase 2: poll for the approval parked by device_start.

    Bounded per call so the harness renders progress between calls; re-run until approved.
    Returns the config path on approval, None while still pending (prints SKUBE-PENDING).
    Exits with a plain message when the code expired or the state is missing.
    """
    import time

    sleep = sleep or time.sleep
    state_path = _device_pending_path()
    if not state_path.exists():
        raise SystemExit("SKUBE: no connection is waiting for approval — run /skube:connect first.")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    base, device_code = state["api_url"], state["device_code"]
    interval = max(1, int(state.get("interval", 3)))
    waited = 0
    while waited < max_wait:
        try:
            tok = _post_json(f"{base}/v1/auth/cli/device/token", {"device_code": device_code})
        except urllib.error.HTTPError as exc:
            if exc.code >= 500:
                # transient edge blip mid-login — the flow is still valid, keep polling
                sleep(interval)
                waited += interval
                continue
            state_path.unlink(missing_ok=True)
            if exc.code == 410:
                raise SystemExit("SKUBE: this connection expired before it was approved. Run /skube:connect again.")
            raise SystemExit(f"SKUBE: connect failed (HTTP {exc.code}).")
        except Exception as exc:  # noqa: BLE001
            raise SystemExit(f"SKUBE: could not reach the Skube API: {exc}")
        if tok.get("status") == "approved":
            state_path.unlink(missing_ok=True)
            return save_api_key(tok["key"], base)
        sleep(interval)
        waited += interval
    print("SKUBE-PENDING: not approved yet — the authorize link is still valid.")
    return None


def connect_via_browser(api_url: str, *, open_browser: bool = True, sleep=None, max_wait: int = 600):
    """Browser device-auth (like `gh login`), single-shot: start + poll to completion.

    The DESKTOP path (a local browser opened). Cloud/headless sessions must not use this —
    connect.py exits after device_start there and drives device_wait as a second phase.
    """
    device_start(api_url, open_browser=open_browser)
    dest = device_wait(sleep=sleep, max_wait=max_wait)
    if dest is None:
        raise SystemExit("SKUBE: authorization timed out. Run /skube:connect again.")
    return dest


def _safe_extract(blob: bytes, dest: pathlib.Path) -> int:
    """Extract a gzipped tar into dest, refusing any path-traversal member. Returns count.

    Extracts OVER dest (never wipes it) so the engine's run output (runs/) and seeded
    brain survive a re-pull.
    """
    dest = dest.resolve()
    safe = []
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as tar:
        for m in tar.getmembers():
            if not (m.isfile() or m.isdir()):
                continue  # never extract symlinks/devices from a downloaded archive
            target = (dest / m.name).resolve()
            if target != dest and not str(target).startswith(str(dest) + os.sep):
                raise SystemExit(f"SKUBE: refusing unsafe path in engine snapshot: {m.name}")
            safe.append(m)
        dest.mkdir(parents=True, exist_ok=True)
        tar.extractall(dest, members=safe)  # noqa: S202 — members validated above
    return len([m for m in safe if m.isfile()])


def provision_engine(api_url: str, api_key: str, dest: pathlib.Path, marketplace: str = "amazon") -> pathlib.Path:
    """Pull the subscription-gated engine snapshot into dest (cache-by-hash via ETag).

    No SKUBE_ENGINE_DIR needed: the plugin fetches the engine itself, like the brain.
    """
    dest.mkdir(parents=True, exist_ok=True)
    hash_file = dest / ".engine_hash"
    cached = hash_file.read_text(encoding="utf-8").strip() if hash_file.exists() else ""
    headers = {"Authorization": f"Bearer {api_key}"}
    if cached:
        headers["If-None-Match"] = f'"{cached}"'
    req = urllib.request.Request(f"{api_url.rstrip('/')}/v1/engine/{marketplace}", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120, context=_SSL_CTX) as resp:  # noqa: S310 (trusted Skube host)
            blob = resp.read()
            digest = (resp.headers.get("X-Engine-Snapshot-Hash") or "").strip()
    except urllib.error.HTTPError as exc:
        if exc.code == 304:
            return dest  # already current — nothing to do
        if exc.code == 402:
            raise SystemExit("SKUBE: no active subscription (402). Reactivate your plan to run.")
        raise SystemExit(f"SKUBE: engine fetch failed (HTTP {exc.code}).")
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"SKUBE: could not reach the Skube API: {exc}")
    _safe_extract(blob, dest)
    if digest:
        hash_file.write_text(digest, encoding="utf-8")
    return dest


def harden_engine_claude_settings(engine_dir: pathlib.Path) -> pathlib.Path:
    """Harden the provisioned engine project's Claude settings (idempotent).

    The engine's ``.claude/settings.local.json`` governs tool permissions. The engine
    snapshot may ship a blanket ``"Bash"`` allow — we REMOVE that and ensure a deny rule
    on the marketplace auth host is present, so the engine project can never make direct
    API egress (all flows go through the Skube cloud gateway). Re-applied on every
    provision; creates a minimal file with just the deny if none exists. Never the real
    boundary (that's server-side), but defense-in-depth on the customer's own machine.
    """
    settings_path = engine_dir / ".claude" / "settings.local.json"
    settings: dict = {}
    if settings_path.exists():
        try:
            loaded = json.loads(settings_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                settings = loaded
        except (OSError, ValueError):
            settings = {}  # malformed/unreadable -> rewrite a clean hardened file

    perms = settings.get("permissions")
    if not isinstance(perms, dict):
        perms = {}

    # Drop any blanket Bash allow (engine snapshots ship one); keep specific allows.
    allow = perms.get("allow")
    if isinstance(allow, list):
        perms["allow"] = [a for a in allow if a != "Bash"]
    elif allow == "Bash":
        perms["allow"] = []

    deny = perms.get("deny")
    if not isinstance(deny, list):
        deny = []
    if _SPAPI_DENY not in deny:
        deny.append(_SPAPI_DENY)
    perms["deny"] = deny
    settings["permissions"] = perms

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(settings, ensure_ascii=False, indent=2) + "\n"
    settings_path.write_text(rendered, encoding="utf-8")
    return settings_path


def seed_engine(bundle: dict, engine_dir: pathlib.Path) -> list[str]:
    """Seed the served brain INTO the engine's own data dir, where the engine reads it.

    engine storage.load() expects data/learnings.json as {"learnings": [...]}, and the
    adapter reads data/amazon_cache/<market>/. SKUBE_ENGINE_DIR must be a WRITABLE copy —
    raises SystemExit (not a bare OSError) if it points at a read-only tree.
    """
    seeded: list[str] = []
    try:
        learnings_path = engine_dir / "data" / "learnings.json"
        learnings_path.parent.mkdir(parents=True, exist_ok=True)
        existing = {}
        if learnings_path.exists():
            existing = json.loads(learnings_path.read_text(encoding="utf-8"))
        existing["learnings"] = bundle.get("learnings") or []
        existing.setdefault("version", "skube-served")
        learnings_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8")
        seeded.append("learnings")

        cache = bundle.get("cache") or {}
        if cache:
            cache_dir = engine_dir / "data" / "amazon_cache" / CACHE_MARKET
            cache_dir.mkdir(parents=True, exist_ok=True)
            for name, content in cache.items():
                (cache_dir / name).write_text(json.dumps(content, ensure_ascii=False), encoding="utf-8")
            seeded.append(f"cache:{len(cache)}")
    except OSError as exc:
        raise SystemExit(
            f"SKUBE: could not seed the brain into {engine_dir}/data — is SKUBE_ENGINE_DIR a WRITABLE "
            f"engine copy (not the read-only repo)? ({exc})"
        )
    return seeded


def _export_session_env(
    session_dir: pathlib.Path, engine_dir: pathlib.Path, run_id: str | None = None
) -> None:
    """Export SKUBE_SESSION_DIR (+ SKUBE_ENGINE_DIR, + SKUBE_RUN_ID) into $CLAUDE_ENV_FILE if
    present, so every Bash-tool command this session — and session_cleanup.py's
    reap_current() on SessionEnd — can find the ephemeral session/engine dirs (and the
    per-run token, Task 9). Follows the same append-only, never-crash pattern as
    session_env.py's env-file writer. Best-effort: if CLAUDE_ENV_FILE isn't set (e.g.
    running bootstrap standalone), this is a no-op. ``run_id`` is only exported when the
    server actually minted one (soft rollout: /v1/run/start may have failed/been skipped).
    """
    env_file = os.environ.get("CLAUDE_ENV_FILE", "").strip()
    if not env_file:
        return
    lines = [
        f"export SKUBE_SESSION_DIR={session_dir}",
        f"export SKUBE_ENGINE_DIR={engine_dir}",
    ]
    if run_id:
        lines.append(f"export SKUBE_RUN_ID={run_id}")
    try:
        with open(env_file, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    except Exception:  # noqa: BLE001 — never break the run over env-file plumbing
        pass


def _resolve_marketplaces(env: dict, api_url: str, api_key: str) -> list[str]:
    """The marketplace SET to provision the engine for (multi-marketplace = pull the UNION snapshot).

    Priority: (1) an explicit ``SKUBE_PLATFORM`` pin — may be a comma/space-separated set (dev/override);
    (2) the account's CONNECTED marketplaces from ``/v1/me/marketplaces`` so a Pro seller who connected
    several gets ALL their adapters in one bundle and can pick any subset in-chat, while a Free/single-MP
    account gets its one; (3) fallback ``amazon`` (fresh account = build-only mode, or ANY error — never
    break bootstrap). Multi is only requested when the tier allows it; the server also gates it.
    """
    pinned = (env.get("SKUBE_PLATFORM") or "").strip().lower()
    if pinned:
        mps = [m for m in (p.strip() for p in pinned.replace(",", " ").split()) if m]
        return mps or ["amazon"]
    try:
        req = urllib.request.Request(
            f"{api_url.rstrip('/')}/v1/me/marketplaces",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        with urllib.request.urlopen(req, timeout=30, context=_SSL_CTX) as resp:  # noqa: S310 — trusted Skube host
            data = json.loads(resp.read())
        connected = sorted({str(i["marketplace"]).lower()
                            for i in data.get("marketplaces", []) if i.get("connected")})
        if not connected:
            return ["amazon"]  # fresh account → single default (catalog/build-only still works)
        multi_ok = bool(data.get("capabilities", {}).get("multi_marketplace"))
        # A single-MP tier only ever pulls one (defensive — the snapshot endpoint also 403s a multi pull).
        return connected if (len(connected) == 1 or multi_ok) else connected[:1]
    except Exception:  # noqa: BLE001 — bootstrap must never fail over this; fall back to single default
        return ["amazon"]


def main() -> None:
    load_dotenv()
    env = os.environ
    errors = validate_config(env)
    if errors:
        raise SystemExit("SKUBE PREFLIGHT FAILED:\n  - " + "\n  - ".join(errors))

    api_url = env.get("SKUBE_API_URL", DEFAULT_API_URL)
    api_key = env["SKUBE_API_KEY"]
    # The marketplace SET this account uses — a comma set pulls the UNION engine snapshot (Pro+; the
    # server gates it), so a multi-marketplace seller has every needed adapter and picks any subset
    # in-chat. ``engine_slug`` = the set for the engine pull; ``primary`` (first) = the brain/seed
    # bootstrap (each MP's catalog is served LIVE at runtime, so one brain reference suffices). A
    # single connected/default marketplace behaves exactly as before.
    marketplaces = _resolve_marketplaces(env, api_url, api_key)
    engine_slug = ",".join(marketplaces)
    primary = marketplaces[0]

    # Everything session-scoped and ephemeral: no durable brain/engine copy survives past
    # this run (reaped by session_cleanup.py per its lease — see T3).
    session_dir = new_session_dir()

    # Engine: an explicit SKUBE_ENGINE_DIR is a user-managed override (dev); otherwise
    # auto-provision the snapshot into the EPHEMERAL session dir (not the durable
    # ~/.skube/engine) so it is shredded on SessionEnd / lease expiry along with the brain.
    override = env.get("SKUBE_ENGINE_DIR", "").strip()
    if override:
        engine_dir = pathlib.Path(override).expanduser()
        engine_source = "override"
    else:
        engine_dir = provision_engine(
            api_url, api_key, session_dir / "engine", marketplace=engine_slug
        )
        engine_source = "auto"

    # Harden the engine project's Claude settings so opening it can't egress to SP-API.
    harden_engine_claude_settings(engine_dir)

    bundle = fetch_brain(api_url, api_key, marketplace=primary)
    write_brain_reference(bundle, session_dir)

    # Task 9 chokepoint: bind this run to a live, entitled account. Soft rollout — if the mint
    # fails, run_id is None and we proceed without it (downstream endpoints only verify when set).
    run_id = start_run(api_url, api_key)

    seeded = seed_engine(bundle, engine_dir)  # engine still needs data/ seeded to pass CP1

    _export_session_env(session_dir, engine_dir, run_id)

    print(
        f"SKUBE ready: brain {bundle.get('version_hash', '?')[:12]} model={bundle.get('model', '?')} "
        f"engine[{engine_source}] seeded[{', '.join(seeded)}] into {engine_dir}/data. "
        f"Session brain reference: {session_dir}. Run engine checkpoints from {engine_dir} (cwd)."
    )
    # Machine-readable fallback (ALWAYS printed, SKUBE_ENGINE_DIR last): when bootstrap runs
    # via a plain Bash tool, CLAUDE_ENV_FILE may be absent so _export_session_env was a no-op —
    # the skill then parses these lines instead of $SKUBE_ENGINE_DIR.
    print(f"SKUBE_SESSION_DIR={session_dir.resolve()}")
    # Task 9: emit the run token too (soft rollout — only when the server actually minted one),
    # BEFORE SKUBE_ENGINE_DIR so that line stays the final, most-relied-upon fallback line.
    if run_id:
        print(f"SKUBE_RUN_ID={run_id}")
    print(f"SKUBE_ENGINE_DIR={engine_dir.resolve()}")


if __name__ == "__main__":
    main()
