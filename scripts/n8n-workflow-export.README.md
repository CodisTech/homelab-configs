# n8n-workflow-export

Auto-mirror n8n workflows from live → Gitea. Closes the drift loop where
UI edits would otherwise stay only in n8n's SQLite database and silently
diverge from the committed source-of-truth.

## Why this exists

Francis stopped firing 2026-05-11 → 2026-05-15 because a UI edit added
backticks that broke n8n's expression parser. The committed `workflow.json`
in `n8n/workflows/francis/` had been stale since 2026-05-09 — the breaking
edit lived only in n8n's database, undetected for 5 days.

After this script is running, the most recent commit to `n8n/exports/` IS
the live workflow state. If a workflow breaks, `git log -p n8n/exports/`
shows what changed and when.

## Where it runs

- **Host**: VM 108 (10.0.60.108) — Claude Code box, has Gitea push access
- **Schedule**: daily 13:00 UTC via systemd timer (1h after Francis fires)
- **User**: `serveradmin`
- **Output**: `n8n/exports/<slug>__<n8n-id>.json`, one file per workflow

The `<slug>__<id>` naming gives human-readable filenames (slug is rebuilt
from workflow name on every run) while keeping the n8n ID for stability
(renaming a workflow in the UI doesn't orphan its export).

## Coexists with `n8n/workflows/<name>/` directories

The curated dirs like `n8n/workflows/francis/` stay — they hold the README,
companion Python scripts (`francis-export-wazuh.py`), systemd units, etc.
The auto-exports in `n8n/exports/` are the raw live state. Both have value:

- `n8n/workflows/<name>/` — **human-maintained** documentation + supporting files
- `n8n/exports/<slug>__<id>.json` — **machine-maintained** state mirror

If they diverge, the export is authoritative for what's *running* right now.

## Install (on VM 108)

```bash
# 1. API key (read once from n8n SQLite, store mode 600)
mkdir -p ~/.config/n8n-export
KEY=$(ssh serveradmin@10.0.60.11 "sudo sqlite3 /home/serveradmin/docker_volumes/n8n/data/database.sqlite \"SELECT apiKey FROM user_api_keys WHERE label='n8n API';\"")
cat > ~/.config/n8n-export/env <<EOF
N8N_API_KEY=$KEY
EOF
chmod 600 ~/.config/n8n-export/env

# 2. systemd units (root install — units live in /etc/systemd/system)
sudo cp /home/serveradmin/work/repos/homelab-configs/scripts/n8n-workflow-export.service /etc/systemd/system/
sudo cp /home/serveradmin/work/repos/homelab-configs/scripts/n8n-workflow-export.timer /etc/systemd/system/
sudo systemctl daemon-reload

# 3. Enable timer
sudo systemctl enable --now n8n-workflow-export.timer

# 4. Verify
systemctl status n8n-workflow-export.timer
systemctl list-timers n8n-workflow-export.timer
```

## Manual run

```bash
N8N_API_KEY=$(cat ~/.config/n8n-export/env | grep N8N_API_KEY | cut -d= -f2-) \
    /home/serveradmin/work/repos/homelab-configs/scripts/n8n-workflow-export.py
```

Or:

```bash
sudo systemctl start n8n-workflow-export.service
journalctl -u n8n-workflow-export.service -n 50
```

## Env vars

| Var | Default | Purpose |
|---|---|---|
| `N8N_API_KEY` | (required) | n8n REST API key |
| `N8N_URL` | `http://10.0.60.11:5678/api/v1` | n8n base URL |
| `HOMELAB_CONFIGS_REPO` | `/home/serveradmin/work/repos/homelab-configs` | Local repo clone (must have push) |
| `GIT_REMOTE` | `origin` | git remote to push |
| `GIT_BRANCH` | `main` | git branch |
| `DRY_RUN` | (off) | When set to `1`/`true`/`yes`: report what would change, don't write/commit/push |

## Volatile fields stripped

These change on every save but carry no semantic content. Stripping them
means cosmetic re-saves don't churn the git history:

- `versionId`, `activeVersionId`, `versionCounter`, `activeVersion`
- `createdAt`, `updatedAt`
- `triggerCount`
- `homeProject`, `shared`, `scopes`, `usedCredentials`
- `tags` are flattened to a sorted list of names (rather than full tag objects with their own timestamps)

## When NOT to rely on this

- **Same-day breakage**: if a workflow breaks at 09:00 ET and the timer
  hasn't fired yet, the committed export is yesterday's. Manual run with
  `systemctl start n8n-workflow-export.service` captures the current state.
- **Pre-edit baseline**: this records state AFTER an edit. To get the
  state BEFORE breaking it, use `git log -p n8n/exports/<file>` to see the
  prior commit.
