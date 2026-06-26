"""Auto-loaded by every Python interpreter that has this dir on PYTHONPATH (W6-T1).

When the plugin runs the engine on a customer machine with ``SKUBE_GATEWAY=true`` (and
this dir injected onto ``PYTHONPATH``), every ``python`` the agent spawns activates the
gateway redirect before running any engine code: the engine's Amazon SP-API calls go to
the Skube cloud, so NO local ``AMAZON_SP_*`` credentials are needed.

Inert unless ``SKUBE_GATEWAY=true``. Must never raise — a failing ``sitecustomize`` would
break the interpreter; activation is wrapped so it can only ever no-op on failure.
"""

import os

if os.environ.get("SKUBE_GATEWAY", "").strip().lower() == "true":
    try:
        import gateway_redirect

        gateway_redirect.activate()
    except Exception:
        pass
