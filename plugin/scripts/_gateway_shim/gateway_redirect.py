"""Redirect the engine's Amazon SP-API calls to the Skube CLOUD gateway (W6-T1).

In Richtung B the engine runs on the CUSTOMER's machine, but Amazon credentials and
every SP-API call MUST stay server-side. This shim makes that transparent: when
``SKUBE_GATEWAY=true`` (see the sibling ``sitecustomize.py``), it monkeypatches the
engine's ``core.amazon_api.AmazonAPI`` so each method calls the Skube cloud over HTTP
instead of Amazon — so the engine needs NO local ``AMAZON_SP_*`` creds at all.

It MUST be self-contained (stdlib only — HTTP via ``urllib.request``, no hard
``requests`` dependency) so it works in a subprocess whose ``sys.path`` is just the
shim dir + site-packages, and it MUST NEVER raise at import time (``sitecustomize``
failing would break the interpreter). All failures happen inside ``activate()`` or the
patched methods, never at import.

Mirrors the proven pattern in ``runner/runner/_dryrun_shim/dryrun_guard.py``:
never-raise-at-import, idempotent monkeypatch, plus a ``requests.Session.send``
backstop. That backstop refuses any direct Amazon egress made through ``requests`` —
which is how the engine performs every SP-API / LWA call, so the engine's own egress is
blocked. It does NOT catch a hand-rolled ``urllib`` / ``http.client`` call straight to
SP-API (those bypass ``requests.Session.send`` entirely) — the same known limitation as
the dry-run shim. The primary protection is the method monkeypatch; the backstop is a
defence-in-depth net for the engine's ``requests`` traffic.
"""

from __future__ import annotations

import base64
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


def _ca_ssl_context() -> ssl.SSLContext:
    """CA bundle for HTTPS. python.org Python on macOS ships NO CA certs, so the stdlib
    default context fails every HTTPS request with CERTIFICATE_VERIFY_FAILED — this hit
    both the shim's own gateway calls AND the engine's direct urllib calls (browse_search,
    product_type_def). Mirror of bootstrap._ca_ssl_context: certifi if importable, else a
    known system bundle, else the stdlib default. Verification is never disabled."""
    try:
        import certifi  # noqa: PLC0415 — optional, guarded; never a hard dependency
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:  # noqa: BLE001
        pass
    for _path in (
        "/etc/ssl/cert.pem",
        "/etc/ssl/certs/ca-certificates.crt",
        "/etc/pki/tls/certs/ca-bundle.crt",
        "/usr/local/etc/openssl/cert.pem",
    ):
        if os.path.exists(_path):
            try:
                return ssl.create_default_context(cafile=_path)
            except Exception:  # noqa: BLE001
                continue
    return ssl.create_default_context()


_SSL_CTX = _ca_ssl_context()


def _install_https_ca_opener() -> bool:
    """Process-wide urllib opener with the resolved CA bundle, so ENGINE code doing its own
    plain ``urllib.request.urlopen`` (browse_search._via_server, product_type_def, …) gets
    working certificate verification too — the engine tree is read-only, so this is the
    sanctioned place to fix it. Never raises."""
    try:
        opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=_SSL_CTX))
        urllib.request.install_opener(opener)
        return True
    except Exception:  # noqa: BLE001
        return False

VALIDATION_PREVIEW = "VALIDATION_PREVIEW"
_DEFAULT_API_URL = "https://api.skube.app"
_DEFAULT_MARKETPLACE = "DE"
_TIMEOUT = 60
FRESHNESS_HEADER = "X-Skube-Freshness"
REFRESH_HINT_HEADER = "X-Skube-Refresh"

# Resolved once, then cached for the life of the process (avoids a /v1/credentials
# round-trip on every patched call).
_credential_id: str | None = None

# The on-disk freshness token (T6's freshness.json), read once per process. ``False``
# means "already looked, nothing usable" so a missing/unreadable file doesn't re-stat
# on every CP2 call. See _freshness_header().
_freshness_header_cache: str | bool | None = None


# ---- Skube cloud config (read lazily, never at import) ----------------------


def _api_url() -> str:
    return (os.environ.get("SKUBE_API_URL") or _DEFAULT_API_URL).rstrip("/")


def _api_key() -> str:
    return os.environ.get("SKUBE_API_KEY", "")


def _marketplace() -> str:
    return os.environ.get("SKUBE_MARKETPLACE") or _DEFAULT_MARKETPLACE


# ---- freshness token (T7: CP2 gateway freshness) -----------------------------
# Read ``freshness.json`` (written by bootstrap.py under SKUBE_SESSION_DIR) once per
# process and attach it as a header on the CP2 product-type calls. Never crashes the
# run: any missing env var / missing file / unreadable JSON just means no header.


def _freshness_header_cache_reset() -> None:
    """Test-only: clear the lazy per-process cache so a test can change the on-disk
    token / SKUBE_SESSION_DIR and see it picked up again."""
    global _freshness_header_cache
    _freshness_header_cache = None


def _freshness_header() -> str | None:
    global _freshness_header_cache
    if _freshness_header_cache is not None:
        return _freshness_header_cache or None
    session_dir = (os.environ.get("SKUBE_SESSION_DIR") or "").strip()
    if not session_dir:
        _freshness_header_cache = False
        return None
    try:
        with open(os.path.join(session_dir, "freshness.json"), "r", encoding="utf-8") as fh:
            raw = fh.read()
        token = json.loads(raw)
        encoded = base64.b64encode(json.dumps(token).encode("utf-8")).decode("ascii")
    except Exception:  # noqa: BLE001 — never crash the run over a missing/bad token file
        _freshness_header_cache = False
        return None
    _freshness_header_cache = encoded
    return encoded


def _note_refresh_hint(headers) -> None:  # noqa: ANN001
    """Debug-level telemetry only: if the cloud says the local brain copy is stale, log
    one line. No auto-re-pull here — the next SessionStart re-pulls (that's the design).
    """
    try:
        if headers.get(REFRESH_HINT_HEADER) == "1":
            print("skube gateway: brain freshness stale, re-pull on next session start",
                  file=sys.stderr)
    except Exception:  # noqa: BLE001 — telemetry must never crash the run
        pass


# ---- session-lease heartbeat --------------------------------------------------
# bootstrap.py leases the ephemeral session dir for 24h; a session that runs LONGER than
# the lease would have its engine reaped mid-run by another window's SessionStart reap.
# So every gateway call best-effort re-stamps the lease to now+24h. Deliberately not
# cached: the whole point is that it keeps re-stamping for the life of the session.

_LEASE_TTL_SECONDS = 24 * 3600  # must match bootstrap.py's _SESSION_TTL_SECONDS
_LEASE_REFRESH_SLACK = 5 * 60  # skip the disk write if the lease was stamped < ~5 min ago


def _heartbeat_lease() -> None:
    """Re-stamp ``<SKUBE_SESSION_DIR>/.skube_lease`` to now+24h. MUST never raise — a
    lease hiccup can never be allowed to break a gateway call."""
    try:
        session_dir = (os.environ.get("SKUBE_SESSION_DIR") or "").strip()
        if not session_dir:
            return
        lease = os.path.join(session_dir, ".skube_lease")
        if not os.path.exists(lease):
            return
        new_expiry = time.time() + _LEASE_TTL_SECONDS
        try:
            with open(lease, "r", encoding="utf-8") as fh:
                current = float(fh.read().strip())
        except Exception:  # noqa: BLE001 — unreadable stamp -> just re-stamp it
            current = 0.0
        if new_expiry - current < _LEASE_REFRESH_SLACK:
            return  # stamped recently — skip the write, keep calls cheap
        with open(lease, "w", encoding="utf-8") as fh:
            fh.write(str(new_expiry))
    except Exception:  # noqa: BLE001 — heartbeat is best-effort, never breaks the call
        pass


# ---- error mapping ----------------------------------------------------------
# Preserve the engine's catch contract: engine code does ``except AmazonAPIError`` /
# ``except AmazonAuthError`` around SP-API calls, so gateway failures must raise THOSE
# types to flow through the engine's existing error handling. If the engine isn't
# importable (e.g. in tests), fall back to RuntimeError.


def _engine_exc(auth: bool):  # noqa: ANN201
    """Return the engine's exception class to raise (or RuntimeError as a fallback).

    ``auth=True`` -> ``AmazonAuthError`` (401/403); else ``AmazonAPIError``.
    """
    try:
        import importlib

        module = importlib.import_module("core.amazon_api")
        name = "AmazonAuthError" if auth else "AmazonAPIError"
        exc = getattr(module, name, None)
        if isinstance(exc, type) and issubclass(exc, Exception):
            return exc
    except Exception:
        pass
    return RuntimeError


# ---- HTTP helpers (stdlib urllib only) --------------------------------------


def _request(
    method: str, path: str, *, params: dict | None = None, body: dict | None = None,
    extra_headers: dict | None = None,
):
    """Call the Skube cloud and return the decoded-JSON response.

    ``Authorization: Bearer {SKUBE_API_KEY}`` is sent on every request. JSON bodies
    are POSTed; query params are URL-encoded onto the path. ``extra_headers`` lets a
    specific call (CP2's product-type endpoints) attach the freshness token without
    every gateway call carrying it.

    Error handling (never leaks the SKUBE_API_KEY):
    - HTTP 4xx/5xx -> read the cloud's response body, surface its JSON ``detail``;
      402 gets a "reactivate your plan" hint; 401/403 raise ``AmazonAuthError``,
      everything else raises ``AmazonAPIError`` (engine catch contract preserved).
    - Network/DNS failure -> a clear "could not reach the Skube cloud" error.
    """
    _heartbeat_lease()  # per-call, best-effort — see the heartbeat section above
    url = _api_url() + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = None
    headers = {"Authorization": f"Bearer {_api_key()}", "Accept": "application/json"}
    if extra_headers:
        headers.update(extra_headers)
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT, context=_SSL_CTX) as resp:
            raw = resp.read()
            _note_refresh_hint(getattr(resp, "headers", {}) or {})
    except urllib.error.HTTPError as e:
        raise _http_error(e) from None
    except urllib.error.URLError as e:
        # Network / DNS down — the cloud was never reached.
        reason = getattr(e, "reason", e)
        raise _engine_exc(auth=False)(
            f"Skube gateway: could not reach the Skube cloud ({reason})."
        ) from None
    return json.loads(raw.decode("utf-8")) if raw else None


def _http_error(e: urllib.error.HTTPError) -> Exception:
    """Build a clear, key-free exception from an HTTPError, surfacing the cloud detail.

    The cloud returns errors as JSON ``{"detail": "..."}``; we read and include that so
    the user sees the actual reason instead of a bare ``HTTP 4xx``. 402 (subscription
    inactive) gets a reactivation hint. The exception TYPE follows the engine's catch
    contract: 401/403 -> AmazonAuthError, else AmazonAPIError.
    """
    status = e.code
    detail = ""
    try:
        payload = json.loads(e.read().decode("utf-8"))
        if isinstance(payload, dict):
            detail = str(payload.get("detail") or "")
    except Exception:
        detail = ""

    if status == 402:
        msg = (
            "Your Skube subscription is inactive — reactivate your plan to keep using "
            "Skube."
        )
        if detail:
            msg += f" ({detail})"
    elif status in (401, 403):
        msg = "Skube gateway: authentication failed (HTTP %d)" % status
        msg += f": {detail}" if detail else " — check your Skube API key."
    else:
        msg = f"Skube gateway: cloud returned HTTP {status}"
        if detail:
            msg += f": {detail}"

    return _engine_exc(auth=status in (401, 403))(msg)


def _resolve_credential_id() -> str:
    """Return the credential id pinned for THIS run — never guessing among several.

    The session picks ONE connection and pins it via ``SKUBE_CREDENTIAL_ID``. This is
    safety-critical for agencies that hold several accounts for the SAME marketplace (one per
    client): products must NEVER cross accounts. So:
      * if a credential is pinned → use exactly that;
      * else, fall back ONLY when there is exactly one matching credential;
      * if several match → REFUSE (the run must pin a connection) rather than risk the wrong account.
    """
    global _credential_id
    if _credential_id is not None:
        return _credential_id
    pinned = (os.environ.get("SKUBE_CREDENTIAL_ID") or "").strip()
    if pinned:
        _credential_id = pinned
        return _credential_id
    platform = (os.environ.get("SKUBE_PLATFORM") or "amazon").strip().lower()
    creds = _request("GET", "/v1/credentials") or []
    matching = [str(e["id"]) for e in creds if isinstance(e, dict) and e.get("marketplace") == platform]
    if len(matching) == 1:
        _credential_id = matching[0]
        return _credential_id
    if not matching:
        raise RuntimeError(
            f"No {platform} connection found in the Skube vault. Connect one in Skube before running."
        )
    raise RuntimeError(
        f"{len(matching)} {platform} connections exist — this run must pin ONE connection "
        "(set SKUBE_CREDENTIAL_ID) so products never land in the wrong account. "
        "Pick the connection at session start."
    )


# ---- redirected method implementations --------------------------------------
# Signatures mirror engine/core/amazon_api.py exactly. ``self`` is the bare engine
# instance (unused — every call is redirected to the Skube cloud).


def _freshness_extra_headers() -> dict | None:
    token = _freshness_header()
    return {FRESHNESS_HEADER: token} if token else None


def _search_product_types(self, marketplace_id=None, keywords=None, force_refresh=False):  # noqa: ANN001
    params = {"credential_id": _resolve_credential_id(), "marketplace": _marketplace()}
    if keywords:
        params["keywords"] = ",".join(keywords)
    out = _request(
        "GET", "/v1/amazon/product-types", params=params, extra_headers=_freshness_extra_headers()
    )
    return (out or {}).get("product_types", [])  # engine contract: List[str]


def _get_product_type_definition(self, product_type, marketplace_id=None, force_refresh=False):  # noqa: ANN001
    params = {"credential_id": _resolve_credential_id(), "marketplace": _marketplace()}
    quoted = urllib.parse.quote(str(product_type), safe="")
    return _request(
        "GET", f"/v1/amazon/product-type/{quoted}", params=params,
        extra_headers=_freshness_extra_headers(),
    )


def _get_listings_item(self, seller_id, sku, marketplace_ids, included_data=None):  # noqa: ANN001
    # CONTRACT NARROWING: the real engine method supports the full Listings Items
    # GET (summaries/attributes/issues/offers via ``included_data``). The current
    # gateway only exposes the ISSUES subset (``/v1/amazon/listings/{sku}/issues``),
    # so ``included_data`` is intentionally IGNORED and we always return issues only.
    # Richer included_data would require a new gateway endpoint — NOT built here.
    params = {"credential_id": _resolve_credential_id(), "marketplace": _marketplace()}
    quoted = urllib.parse.quote(str(sku), safe="")
    return _request("GET", f"/v1/amazon/listings/{quoted}/issues", params=params)


def _write(op: str, sku, body, mode=None):  # noqa: ANN001
    """Shared put/patch/delete writer. VALIDATION_PREVIEW -> /validate, else /submit."""
    payload = {
        "credential_id": _resolve_credential_id(),
        "marketplace": _marketplace(),
        "sku": sku,
        "op": op,
    }
    if body is not None:
        payload["body"] = body
    path = "/v1/amazon/validate" if (mode or "").upper() == VALIDATION_PREVIEW else "/v1/amazon/submit"
    return _request("POST", path, body=payload)


def _put_listings_item(self, seller_id, sku, marketplace_ids, body, mode=None):  # noqa: ANN001
    return _write("put", sku, body, mode=mode)


def _patch_listings_item(self, seller_id, sku, marketplace_ids, body, mode=None):  # noqa: ANN001
    return _write("patch", sku, body, mode=mode)


def _delete_listings_item(self, seller_id, sku, marketplace_ids):  # noqa: ANN001
    return _write("delete", sku, None, mode=None)


_METHODS = {
    "search_product_types": _search_product_types,
    "get_product_type_definition": _get_product_type_definition,
    "get_listings_item": _get_listings_item,
    "put_listings_item": _put_listings_item,
    "patch_listings_item": _patch_listings_item,
    "delete_listings_item": _delete_listings_item,
}


# ---- activation --------------------------------------------------------------


def _patch_engine_amazon_api() -> bool:
    """Patch ``core.amazon_api.AmazonAPI`` methods + ``from_instance`` in place.

    Best-effort: if the engine isn't importable yet the requests backstop still
    protects egress. Returns True if the class was patched. Idempotent.
    """
    import importlib

    module = importlib.import_module("core.amazon_api")
    cls = getattr(module, "AmazonAPI", None)
    if cls is None:
        return False
    if getattr(cls, "_skube_gateway_patched", False):
        return True

    for name, fn in _METHODS.items():
        setattr(cls, name, fn)

    # from_instance must return an instance EVEN WHEN AMAZON_SP_* are missing (the real
    # engine raises AmazonAuthError there). Creds are unused — every method is redirected.
    # Signature matches the engine's classmethod: (cls, instance_config, **kwargs).
    def _from_instance(klass, instance_config, **kwargs):  # noqa: ANN001
        return klass.__new__(klass)

    cls.from_instance = classmethod(_from_instance)
    cls._skube_gateway_patched = True
    return True


def _patch_payload_builder_validate() -> bool:
    """Patch ``core.amazon_payload_builder.AmazonPayloadBuilder.validate_payload`` so the
    authoritative required-fields + enum check runs SERVER-SIDE against the LIVE schema
    (Task 10: ``POST /v1/{mp}/validate-payload``) instead of against the client's local
    ``valid_values`` copy (which Task 11 stops shipping).

    FAIL-SAFE (removed by Task 13): if the gateway is unreachable, the API key is unset,
    or the response is malformed, fall back to the ORIGINAL local validation — a server
    hiccup must never crash a run mid-CP6. Best-effort + idempotent, like the API patch.
    """
    import importlib

    module = importlib.import_module("core.amazon_payload_builder")
    cls = getattr(module, "AmazonPayloadBuilder", None)
    result_cls = getattr(module, "ValidationResult", None)
    if cls is None or result_cls is None:
        return False
    if getattr(cls, "_skube_validate_redirected", False):
        return True
    local_validate = cls.validate_payload

    def _remote_validate(self, payload, mode):  # noqa: ANN001
        try:
            if not _api_key():
                return local_validate(self, payload, mode)
            mp = (os.environ.get("SKUBE_PLATFORM") or "amazon").strip().lower()
            params = {"credential_id": _resolve_credential_id(), "marketplace": _marketplace()}
            extra = {}
            run_id = (os.environ.get("SKUBE_RUN_ID") or "").strip()
            if run_id:
                extra["X-Skube-Run-Id"] = run_id
            mode_str = getattr(mode, "value", None) or str(mode)
            out = _request(
                "POST",
                f"/v1/{mp}/validate-payload",
                params=params,
                body={
                    "product_type": getattr(self, "product_type", None),
                    "payload": payload,
                    "mode": mode_str,
                },
                extra_headers=extra or None,
            )
            if not isinstance(out, dict) or "ok" not in out:
                raise ValueError("malformed validate-payload response")
            return result_cls(
                valid=bool(out.get("ok")),
                errors=list(out.get("errors") or []),
                warnings=list(out.get("warnings") or []),
                stats=dict(out.get("stats") or {}),
            )
        except Exception:  # noqa: BLE001 — fail-safe fallback; Task 13 removes it
            return local_validate(self, payload, mode)

    cls.validate_payload = _remote_validate
    cls._skube_validate_redirected = True
    return True


def _install_requests_backstop() -> bool:
    """Patch ``requests.Session.send`` to REFUSE any direct Amazon SP-API / LWA egress.

    Best-effort and guarded: if ``requests`` isn't importable, skip gracefully. Mirrors
    the dry-run shim's single-chokepoint backstop so a hand-rolled HTTP call can't bypass
    the gateway. Idempotent.
    """
    try:
        import functools

        import requests.sessions as _sessions
    except Exception:
        return False

    if getattr(_sessions.Session, "_skube_gateway_guarded", False):
        return True
    original_send = _sessions.Session.send

    @functools.wraps(original_send)
    def guarded_send(self, request, **kwargs):  # noqa: ANN001
        url = getattr(request, "url", "") or ""
        host = urllib.parse.urlparse(url).netloc.lower()
        if "sellingpartnerapi" in host or "api.amazon.com/auth" in url.lower():
            raise RuntimeError(
                "Skube gateway: direct Amazon SP-API is not allowed; use the Skube "
                f"gateway (refused {request.method} {url})."
            )
        return original_send(self, request, **kwargs)

    _sessions.Session.send = guarded_send
    _sessions.Session._skube_gateway_guarded = True
    return True


def activate() -> list[str]:
    """Install the gateway redirect + egress backstop. Returns which layers installed.

    Safe to call more than once. Each layer is independently guarded so a failure in
    one (e.g. the engine not importable yet) never blocks the other.
    """
    installed: list[str] = []
    try:
        if _install_https_ca_opener():
            installed.append("https-ca")
    except Exception:
        pass
    try:
        if _patch_engine_amazon_api():
            installed.append("engine")
    except Exception:
        pass
    try:
        if _patch_payload_builder_validate():
            installed.append("validate")
    except Exception:
        pass
    try:
        if _install_requests_backstop():
            installed.append("requests")
    except Exception:
        pass
    return installed
