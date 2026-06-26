#!/usr/bin/env python3
"""SessionStart hook — activate the Skube gateway shim ONLY in the engine project (W6-T2).

When a Claude Code session opens the auto-provisioned engine project (``~/.skube/engine``),
this writes the env that the gateway shim needs into ``$CLAUDE_ENV_FILE`` so every Bash-tool
``python`` the agent spawns this session picks it up:

    export SKUBE_API_URL=...
    export SKUBE_API_KEY=...        (only if present in ~/.skube/.env)
    export SKUBE_GATEWAY=true
    export PYTHONPATH=<_gateway_shim dir>:<existing PYTHONPATH>

The shim dir on PYTHONPATH + SKUBE_GATEWAY=true is what activates ``sitecustomize.py`` ->
``gateway_redirect.activate()`` (the engine's Amazon SP-API egress is redirected to the Skube
cloud, so NO local AMAZON_SP_* creds are needed).

SCOPING: if the session's project is NOT the engine, this exits 0 doing nothing — it must never
touch the user's other projects. Secrets are only ever written to the env file, never to stdout.
Stdlib only; must never crash (always exits 0).
"""

from __future__ import annotations

import os
import pathlib

DEFAULT_API_URL = "https://api.skube.app"


def _engine_dir() -> pathlib.Path:
    """The auto-provisioned engine project — mirrors bootstrap.DEFAULT_ENGINE_DIR."""
    return pathlib.Path.home() / ".skube" / "engine"


def _is_engine_project(project_dir: str) -> bool:
    """True iff ``project_dir`` IS the Skube engine project.

    Compares realpaths against ``~/.skube/engine``; also accepts any path whose tail is
    ``.skube/engine`` (handles a symlinked/relocated HOME where the realpaths differ but
    the path still clearly names the engine project).
    """
    if not project_dir:
        return False
    try:
        resolved = pathlib.Path(project_dir).expanduser().resolve()
    except Exception:
        return False
    try:
        if resolved == _engine_dir().resolve():
            return True
    except Exception:
        pass
    parts = resolved.parts
    return len(parts) >= 2 and parts[-2] == ".skube" and parts[-1] == "engine"


def _load_dotenv(path: pathlib.Path) -> dict:
    """Tiny KEY=VALUE parser for ~/.skube/.env (never raises). Strips quotes."""
    out: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return out
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def _config_env_path(project_dir: str) -> pathlib.Path:
    """Locate the Skube .env (lk_live_ key). It lives in the ``.skube`` dir next to the engine
    project — i.e. the project's parent — so it works whether ``.skube`` sits in HOME
    (``~/.skube/engine``) or inside the user's allowed workspace (``<repo>/.skube/engine``).
    Falls back to ``~/.skube/.env``.
    """
    try:
        parent_env = pathlib.Path(project_dir).expanduser().resolve().parent / ".env"
        if parent_env.exists():
            return parent_env
    except Exception:
        pass
    return pathlib.Path.home() / ".skube" / ".env"


def _shim_dir() -> str:
    """Absolute path to the _gateway_shim dir.

    Prefers ``${CLAUDE_PLUGIN_ROOT}/scripts/_gateway_shim``; falls back to deriving it from
    this script's own location (this file lives in ``<root>/scripts/``).
    """
    root = os.environ.get("CLAUDE_PLUGIN_ROOT", "").strip()
    if root:
        return str(pathlib.Path(root) / "scripts" / "_gateway_shim")
    return str(pathlib.Path(__file__).resolve().parent / "_gateway_shim")


def main() -> None:
    env_file = os.environ.get("CLAUDE_ENV_FILE", "").strip()
    if not env_file:
        return  # nowhere to write session env — nothing to do
    # Scope strictly to the engine project so other projects are never touched.
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    if not _is_engine_project(project_dir):
        return

    dotenv = _load_dotenv(_config_env_path(project_dir))
    api_url = dotenv.get("SKUBE_API_URL") or DEFAULT_API_URL
    api_key = dotenv.get("SKUBE_API_KEY", "")

    shim = _shim_dir()
    existing_pp = os.environ.get("PYTHONPATH", "")
    pythonpath = f"{shim}:{existing_pp}" if existing_pp else shim

    lines = [f"export SKUBE_API_URL={api_url}"]
    if api_key:
        lines.append(f"export SKUBE_API_KEY={api_key}")
    lines.append("export SKUBE_GATEWAY=true")
    lines.append(f"export PYTHONPATH={pythonpath}")

    try:
        with open(env_file, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    except Exception:
        return  # never crash the session


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
