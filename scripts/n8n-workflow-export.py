#!/usr/bin/env python3
"""
n8n-workflow-export.py — Mirror n8n workflows from live → Gitea.

Closes the drift loop: UI edits to n8n workflows are rounded back into the
homelab-configs repo automatically. If a workflow breaks (like Francis did
2026-05-11 → 2026-05-15 due to backticks), the most recent committed export
is the diagnostic baseline.

Behavior:
  - Fetch all workflows from n8n REST API.
  - For each: write pretty-printed JSON to <repo>/n8n/exports/<id>.json.
  - Strip volatile fields (versionId, updatedAt, lastUsedAt, etc.) so cosmetic
    re-saves don't churn the git history.
  - If any file changed: git add, commit with workflow-name list, push to Gitea.

Designed to run from a systemd timer on VM 108. Idempotent; safe to run manually.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
import urllib3
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ---------------------------------------------------------------------------
# Config — overridable via env
# ---------------------------------------------------------------------------
N8N_URL = os.environ.get("N8N_URL", "http://10.0.60.11:5678/api/v1")
API_KEY = os.environ.get("N8N_API_KEY")
REPO_PATH = Path(os.environ.get("HOMELAB_CONFIGS_REPO",
                                "/home/serveradmin/work/repos/homelab-configs"))
EXPORTS_DIR = REPO_PATH / "n8n" / "exports"
GIT_REMOTE = os.environ.get("GIT_REMOTE", "origin")
GIT_BRANCH = os.environ.get("GIT_BRANCH", "main")
DRY_RUN = os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")

# Fields that change every save but carry no semantic content. Removing them
# eliminates churn — only real workflow edits trigger commits.
VOLATILE_TOP_LEVEL = {
    "versionId", "activeVersionId", "versionCounter",
    "createdAt", "updatedAt",
    "triggerCount",
    "activeVersion",         # n8n 2.4 adds this nested object on GET
    "homeProject", "shared", "scopes", "usedCredentials",
}

# ---------------------------------------------------------------------------

def log(msg: str) -> None:
    print(msg, flush=True)


def slugify(s: str) -> str:
    s = re.sub(r"[^\w\s-]", "", (s or "").lower())
    s = re.sub(r"[\s_-]+", "-", s).strip("-")
    return s or "unknown"


def fetch_all_workflows(session: requests.Session) -> list[dict]:
    """List all workflows (lightweight metadata) then fetch each fully."""
    r = session.get(f"{N8N_URL}/workflows", timeout=10)
    r.raise_for_status()
    listing = r.json().get("data", [])
    full = []
    for meta in listing:
        wid = meta["id"]
        r2 = session.get(f"{N8N_URL}/workflows/{wid}", timeout=10)
        r2.raise_for_status()
        full.append(r2.json())
    return full


def strip_volatile(wf: dict) -> dict:
    """Remove fields that change on every save but carry no semantic content."""
    cleaned = {k: v for k, v in wf.items() if k not in VOLATILE_TOP_LEVEL}
    # tags are nested objects with their own updatedAt/createdAt — flatten to names
    if "tags" in cleaned and isinstance(cleaned["tags"], list):
        cleaned["tags"] = sorted(
            {t.get("name") for t in cleaned["tags"] if isinstance(t, dict) and t.get("name")}
        )
    return cleaned


def write_workflow(wf: dict) -> tuple[Path, bool]:
    """Write workflow JSON to <exports>/<id>.json. Returns (path, changed)."""
    wid = wf["id"]
    slug = slugify(wf.get("name", ""))
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    # Filename = <slug>__<id>.json — slug for human discovery, id for stability.
    path = EXPORTS_DIR / f"{slug}__{wid}.json"
    new = json.dumps(strip_volatile(wf), indent=2, sort_keys=True) + "\n"
    if path.exists() and path.read_text() == new:
        return path, False
    if DRY_RUN:
        log(f"[dry-run] would write {path.relative_to(REPO_PATH)}")
        return path, True
    path.write_text(new)
    return path, True


def cleanup_orphans(live_ids: set[str]) -> list[Path]:
    """Remove exports/*.json whose workflow ID no longer exists in n8n."""
    if not EXPORTS_DIR.exists():
        return []
    removed = []
    for f in EXPORTS_DIR.glob("*.json"):
        m = re.match(r"^(.+)__([A-Za-z0-9]+)\.json$", f.name)
        if not m:
            continue
        wid = m.group(2)
        if wid not in live_ids:
            if not DRY_RUN:
                f.unlink()
            removed.append(f)
            log(f"  removed orphan: {f.relative_to(REPO_PATH)}")
    return removed


def git(*args, check=True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(REPO_PATH), *args],
        check=check, capture_output=True, text=True,
    )


def commit_and_push(changed_files: list[Path], removed_files: list[Path],
                    workflow_names: list[str]) -> bool:
    """Stage + commit + push if there's a real diff. Returns True if commit happened."""
    # Stage all exports/ changes (additions, modifications, deletions)
    git("add", "n8n/exports/")
    # Check if anything is actually staged
    status = git("status", "--porcelain", "n8n/exports/")
    if not status.stdout.strip():
        log("No staged changes after git add (already clean).")
        return False

    n_changed = len(changed_files)
    n_removed = len(removed_files)
    summary = f"{n_changed} updated, {n_removed} removed" if n_removed else f"{n_changed} updated"
    names_list = "\n".join(f"- {n}" for n in sorted(workflow_names))
    msg = (
        f"n8n/exports: auto-sync from live n8n ({summary})\n\n"
        f"Workflows in this snapshot:\n{names_list}\n\n"
        f"Drift mirror: closes the loop on UI edits that would otherwise stay\n"
        f"only in n8n's SQLite. See feedback_n8n_expression_backticks.md for\n"
        f"the failure mode this guards against."
    )
    if DRY_RUN:
        log("[dry-run] would commit:")
        log(msg)
        log("[dry-run] would push to " + f"{GIT_REMOTE}/{GIT_BRANCH}")
        return True

    # Use a fixed author so this doesn't pick up whoever happens to run it
    env = os.environ.copy()
    env["GIT_AUTHOR_NAME"] = "John (Claude Code VM)"
    env["GIT_AUTHOR_EMAIL"] = "john@example.home"
    env["GIT_COMMITTER_NAME"] = "John (Claude Code VM)"
    env["GIT_COMMITTER_EMAIL"] = "john@example.home"
    subprocess.run(
        ["git", "-C", str(REPO_PATH), "commit", "-m", msg],
        check=True, env=env,
    )
    subprocess.run(
        ["git", "-C", str(REPO_PATH), "push", GIT_REMOTE, GIT_BRANCH],
        check=True,
    )
    return True


def main() -> int:
    if not API_KEY:
        log("ERROR: N8N_API_KEY env var not set", )
        return 2
    if not REPO_PATH.exists():
        log(f"ERROR: repo path does not exist: {REPO_PATH}")
        return 2

    session = requests.Session()
    session.headers["X-N8N-API-KEY"] = API_KEY
    session.headers["Accept"] = "application/json"
    session.verify = False  # internal LAN

    log(f"Fetching workflows from {N8N_URL}")
    try:
        workflows = fetch_all_workflows(session)
    except requests.HTTPError as e:
        log(f"ERROR: n8n API returned {e.response.status_code}: {e.response.text[:200]}")
        return 3
    except requests.RequestException as e:
        log(f"ERROR: cannot reach n8n: {e}")
        return 3

    log(f"Got {len(workflows)} workflows")
    changed = []
    names = []
    live_ids = set()
    for wf in workflows:
        live_ids.add(wf["id"])
        names.append(wf.get("name", wf["id"]))
        path, did_change = write_workflow(wf)
        if did_change:
            changed.append(path)
            log(f"  updated: {path.relative_to(REPO_PATH)} ({wf.get('name')})")
    removed = cleanup_orphans(live_ids)

    if not changed and not removed:
        log("No changes — nothing to commit.")
        return 0

    if commit_and_push(changed, removed, names):
        log(f"Committed + pushed to {GIT_REMOTE}/{GIT_BRANCH}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
