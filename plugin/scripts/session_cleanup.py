#!/usr/bin/env python3
"""SessionEnd hook — shred this session's ephemeral engine/brain dir, and reap any
expired leftovers. Stdlib-only; must never crash (always exits 0)."""
from __future__ import annotations
import json, os, pathlib, shutil, time

def _sessions_root() -> pathlib.Path:
    return pathlib.Path.home() / ".skube" / ".sessions"

def _lease_expired(sess: pathlib.Path) -> bool:
    try:
        return time.time() > float((sess / ".skube_lease").read_text(encoding="utf-8").strip())
    except Exception:
        return True  # unreadable/missing lease -> treat as reapable

def reap_expired() -> None:
    root = _sessions_root()
    if not root.is_dir():
        return
    for sess in root.glob("skube-run-*"):
        if sess.is_dir() and _lease_expired(sess):
            shutil.rmtree(sess, ignore_errors=True)

def reap_current() -> None:
    """If the harness told us the session's cwd, and it's a skube-run dir, remove it.

    Containment: the resolved path must actually live under ~/.skube/.sessions/ — a
    skube-run-* NAME alone (from a hostile/buggy SKUBE_SESSION_DIR) must never be enough
    to rmtree an arbitrary location."""
    cur = os.environ.get("SKUBE_SESSION_DIR", "").strip()
    if not cur:
        return
    try:
        p = pathlib.Path(cur).resolve()
        root = _sessions_root().resolve()
    except Exception:
        return
    if p.name.startswith("skube-run-") and p.parent == root and p.is_dir():
        shutil.rmtree(p, ignore_errors=True)

def _project_run_root() -> pathlib.Path | None:
    """Where the create skill puts run DATA so it survives session cleanup:
    <project>/skube-run/ (see plugin/skills/create/SKILL.md CP0). $CLAUDE_PROJECT_DIR
    wins when set and the dir exists; else fall back to cwd/skube-run; else None."""
    proj = os.environ.get("CLAUDE_PROJECT_DIR", "").strip()
    if proj:
        try:
            candidate = pathlib.Path(proj) / "skube-run"
            if candidate.is_dir():
                return candidate
        except Exception:
            pass
    try:
        candidate = pathlib.Path.cwd() / "skube-run"
        if candidate.is_dir():
            return candidate
    except Exception:
        pass
    return None


def _is_run_dir(d: pathlib.Path) -> bool:
    """Conservative marker check — only descend into dirs that look like a real
    skube run, so we never wander into unrelated user folders under skube-run/.
    config.json is a valid marker because CP0 (cp0_setup.py) always writes it into
    every run dir."""
    try:
        return (
            (d / "extracted.json").is_file()
            or (d / "extracted").is_dir()
            or (d / "config.json").is_file()
            or (d / "injected_rules.md").is_file()
        )
    except Exception:
        return False


def _scrub_extracted_json(path: pathlib.Path) -> None:
    """Empty valid_values' value-lists in place; keep every other key/field intact
    so a resumed run can re-fetch values server-side. Best-effort: any failure to
    read/parse/write is silently skipped. Write is atomic (temp+rename) to avoid
    truncation if SessionEnd is killed mid-write."""
    try:
        if not path.is_file():
            return
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return
    try:
        vv = data.get("valid_values")
        if not isinstance(vv, dict):
            return
        for key in list(vv.keys()):
            vv[key] = []
        new_json = json.dumps(data, indent=2, ensure_ascii=False)
        # Atomic write: temp file + os.replace (POSIX atomic rename)
        tmp = path.with_name(path.name + ".skube-tmp")
        try:
            tmp.write_text(new_json, encoding="utf-8")
            os.replace(tmp, path)
        except Exception:
            # Cleanup temp file on failure
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass
            raise
    except Exception:
        return


def scrub_project_run_artifacts() -> None:
    """Scrub the schema-corpus intermediates (extracted.json valid_values,
    injected_rules.md) out of project-folder run dirs at SessionEnd, so the moat
    doesn't persist on disk after the session. Never touches input/ or output/,
    never deletes the run dir itself, never raises."""
    root = _project_run_root()
    if root is None:
        return
    try:
        children = list(root.iterdir())
    except Exception:
        return
    for run in children:
        try:
            if not run.is_dir() or not _is_run_dir(run):
                continue
        except Exception:
            continue
        _scrub_extracted_json(run / "extracted.json")
        _scrub_extracted_json(run / "extracted" / "extracted.json")
        try:
            rules = run / "injected_rules.md"
            if rules.is_file():
                rules.unlink()
        except Exception:
            pass


def main() -> None:
    reap_current()
    reap_expired()
    try:
        scrub_project_run_artifacts()
    except Exception:
        pass

if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
