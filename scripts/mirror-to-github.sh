#!/usr/bin/env bash
# mirror-to-github.sh — clone Gitea homelab-configs, scrub real values, force-push to public GitHub.
# Architecture: Gitea = source of truth (real). GitHub = scrubbed mirror. This is the transform.
# Runs every 5 min via serveradmin's crontab on VM 100. fail-closed on any leak indicator.
#
# Companion script: scripts/sanitize-mirror.sh (runs inside n8n for the k3s-manifests repo on
# Gitea webhook trigger). Same intent, different trigger. See project_github_mirror_inventory.md.
#
# Deploy: copy this file to /home/serveradmin/scripts/mirror-to-github.sh on VM 100, chmod +x,
# add the cron line `*/5 * * * * /home/serveradmin/scripts/mirror-to-github.sh >>$HOME/log/mirror-to-github.cron 2>&1`.

set -Eeuo pipefail

GITEA_URL="git@git.local.example.home:John/homelab-configs.git"
GITHUB_URL="git@github.com:CodisTech/homelab-configs.git"
LOCK="/tmp/mirror-to-github.lock"
LOGFILE="$HOME/log/mirror-to-github.log"
WORKROOT="/tmp/mirror-to-github.work"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { echo "[$(ts)] $*" | tee -a "$LOGFILE"; }
fail() { log "FAIL: $*"; exit 1; }

# Concurrency: drop quietly if another run is in flight.
exec 9>"$LOCK"
if ! flock -n 9; then
  log "another run holds the lock, exiting"
  exit 0
fi

trap 'rm -rf "$WORKROOT"' EXIT

log "===== mirror run start ====="
rm -rf "$WORKROOT"
git clone --depth=1 --quiet "$GITEA_URL" "$WORKROOT" || fail "gitea clone failed"
cd "$WORKROOT"

GITEA_HEAD="$(git rev-parse HEAD)"
log "gitea HEAD: $GITEA_HEAD"

[[ -x ./scrub.sh ]] || fail "scrub.sh missing or not executable in repo"
./scrub.sh --in-place >>"$LOGFILE" 2>&1 || fail "scrub.sh --in-place errored"

# Fail-closed verification: grep for any of the canonical leak markers in the working tree.
# If any survive scrub, abort BEFORE creating the commit that would push them.
# Patterns kept in sync with scrub.sh LEAK_PATTERNS.
if grep -rIE "(local\.codistech\.live|@codistech\.live|192\.168\.[0-9]+\.[0-9]+|\bhvs\.[A-Za-z0-9_.-]{10,}\b|\bs\.[A-Za-z0-9]{24,}\b)" \
     --exclude-dir=.git --exclude=scrub.sh --exclude="*.md" . >/dev/null; then
  log "post-scrub leak found, aborting (no push):"
  grep -rInE "(local\.codistech\.live|@codistech\.live|192\.168\.[0-9]+\.[0-9]+|\bhvs\.[A-Za-z0-9_.-]{10,}\b|\bs\.[A-Za-z0-9]{24,}\b)" \
     --exclude-dir=.git --exclude=scrub.sh --exclude="*.md" . | tee -a "$LOGFILE" | head -20
  fail "leak in post-scrub working tree"
fi

# Orphan-branch single-commit pattern: GitHub gets a flat snapshot, no real-value history visible.
git checkout --orphan mirror-snapshot >>"$LOGFILE" 2>&1
git add -A
git -c user.name="homelab-mirror" -c user.email="mirror@example.home" \
    commit -m "Public mirror snapshot ($(ts)) — gitea $GITEA_HEAD" >>"$LOGFILE" 2>&1

git push --force "$GITHUB_URL" HEAD:main >>"$LOGFILE" 2>&1 || fail "github push failed"

log "===== mirror run OK (gitea $GITEA_HEAD pushed to github main) ====="
