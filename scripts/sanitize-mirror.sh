#!/bin/sh
# sanitize-mirror.sh
# Clones k3s-manifests from Gitea, sanitizes private data, force-pushes to GitHub.
# Called by n8n workflow on Gitea push webhook (workflow id XyvfohalxXsSBNKp).
# Lives in the n8n container at /home/node/.n8n/sanitize-mirror.sh; this copy in
# the homelab-configs repo is the source-of-truth for change tracking and review.
#
# Companion script: scripts/mirror-to-github.sh (cron-driven, for the homelab-configs
# repo itself). Same intent, different trigger. See project_github_mirror_inventory.md.
#
# Env vars (injected by n8n credentials at execution time, not stored in this file):
#   GITEA_TOKEN  — Gitea PAT with read access to k3s-manifests
#   GITHUB_TOKEN — GitHub PAT with write access to CodisTech/k3s-manifests
#
# Deploy: copy this file to /home/node/.n8n/sanitize-mirror.sh inside the n8n
# container (it persists in the n8n data volume), chmod +x.

set -eu

# --- Configuration ---
GITEA_REPO="https://${GITEA_TOKEN}@git.local.example.home/john/k3s-manifests.git"
GITHUB_REPO="https://${GITHUB_TOKEN}@github.com/CodisTech/k3s-manifests.git"
WORK_DIR="/tmp/k3s-mirror-$$"
BRANCH="main"

# --- Functions ---
cleanup() {
    rm -rf "$WORK_DIR"
}
trap cleanup EXIT

log() {
    echo "[$(date -u '+%Y-%m-%dT%H:%M:%SZ')] $1"
}

# --- Main ---
log "Starting Gitea -> GitHub mirror"

# Clone from Gitea
log "Cloning from Gitea..."
git clone --single-branch --branch "$BRANCH" "$GITEA_REPO" "$WORK_DIR" 2>&1
cd "$WORK_DIR"

# Remove git history entirely to avoid secrets in old commits
rm -rf .git

# --- Sanitize ---
log "Sanitizing private data..."

# Find all text files
find . -type f \( -name '*.yaml' -o -name '*.yml' -o -name '*.sh' -o -name '*.md' -o -name '*.json' -o -name '*.txt' -o -name '*.toml' -o -name '*.ini' -o -name '*.cfg' -o -name '*.conf' -o -name '*.env' -o -name '*.properties' \) | while read -r file; do
    # Replace private IP ranges
    sed -i \
        -e 's/192\.168\.60\./10.0.60./g' \
        -e 's/192\.168\.40\./10.0.40./g' \
        -e 's/192\.168\.0\./10.0.0./g' \
        -e 's/192\.168\.99\./10.0.99./g' \
        -e 's/192\.168\.70\./10.0.70./g' \
        "$file"

    # Replace domain
    sed -i 's/codistech\.live/example.home/g' "$file"

    # Replace Vault tokens (hvs. and s. patterns)
    sed -i 's/hvs\.[A-Za-z0-9_.-]\{10,\}/CHANGE_ME/g' "$file"
    sed -i 's/s\.[A-Za-z0-9]\{24,\}/CHANGE_ME/g' "$file"

    # Replace token/secret/password values (quoted strings 20+ chars)
    sed -i -E 's/(token:\s*")[A-Za-z0-9+/=_.:-]{20,}"/\1CHANGE_ME"/g' "$file"
    sed -i -E "s/(token:\s*')[A-Za-z0-9+/=_.:-]{20,}'/\1CHANGE_ME'/g" "$file"
    sed -i -E 's/(secret:\s*")[A-Za-z0-9+/=_.:-]{20,}"/\1CHANGE_ME"/g' "$file"
    sed -i -E 's/(password:\s*")[A-Za-z0-9+/=_.:-]{20,}"/\1CHANGE_ME"/g' "$file"
done

# --- Create fresh single-commit repo ---
log "Creating sanitized commit..."
git init 2>&1
git checkout -b "$BRANCH" 2>&1
git config user.email "n8n@codistech.local"
git config user.name "n8n Mirror Bot"
git add -A
git commit -m "Sanitized mirror of k3s-manifests (auto-synced)" 2>&1

# --- Push to GitHub ---
git remote add origin "$GITHUB_REPO"
log "Force-pushing to GitHub..."
git push --force origin "$BRANCH" 2>&1

log "Mirror complete. GitHub repo updated."
