#!/bin/bash
# sanitize-homelab.sh
# Replaces real internal IPs with generic examples while preserving structure
# Run from the root of the homelab-configs repo
# 
# Mapping:
#   192.168.0.1    (pfSense)     → 10.0.0.1
#   192.168.0.50   (Pi-hole 1)   → 10.0.0.50
#   192.168.0.55   (Pi-hole 2)   → 10.0.0.55
#   192.168.0.70   (Nextcloud)   → 10.0.0.70
#   192.168.0.90   (Proxmox)     → 10.0.0.90
#   192.168.0.100  (Unifi)       → 10.0.0.100
#   192.168.60.0   (VLAN)        → 10.0.60.0
#   192.168.60.11  (Firefly VM)  → 10.0.60.11
#   local.codistech.live          → local.example.home

set -e

REPO_DIR="${1:-.}"
cd "$REPO_DIR"

echo "=== Sanitizing homelab-configs ==="
echo "Working in: $(pwd)"
echo ""

# IP replacements (order matters - longest match first)
declare -a REPLACEMENTS=(
    "192.168.0.100|10.0.0.100"
    "192.168.0.90|10.0.0.90"
    "192.168.0.70|10.0.0.70"
    "192.168.0.55|10.0.0.55"
    "192.168.0.50|10.0.0.50"
    "192.168.0.1|10.0.0.1"
    "192.168.60.11|10.0.60.11"
    "192.168.60.0|10.0.60.0"
    "192.168.x.x|10.0.0.x"
    "local.codistech.live|local.example.home"
    "codistech.live|example.home"
)

# File patterns to process
FILE_PATTERNS="*.yaml *.yml *.env* *.conf *.toml *.md"

for replacement in "${REPLACEMENTS[@]}"; do
    OLD=$(echo "$replacement" | cut -d'|' -f1)
    NEW=$(echo "$replacement" | cut -d'|' -f2)
    
    # Find and replace in all matching files
    COUNT=$(grep -rl "$OLD" --include="*.yaml" --include="*.yml" --include="*.env*" --include="*.conf" --include="*.toml" --include="*.md" . 2>/dev/null | wc -l)
    
    if [ "$COUNT" -gt 0 ]; then
        echo "Replacing: $OLD → $NEW ($COUNT files)"
        find . -type f \( -name "*.yaml" -o -name "*.yml" -o -name "*.env*" -o -name "*.conf" -o -name "*.toml" -o -name "*.md" \) -not -path "./.git/*" -exec sed -i "s|$OLD|$NEW|g" {} +
    fi
done

echo ""
echo "=== Verification ==="
echo "Remaining real IPs (should be 0):"
grep -rn "192\.168\." --include="*.yaml" --include="*.yml" --include="*.env*" --include="*.conf" --include="*.toml" . 2>/dev/null | grep -v ".git" | wc -l

echo ""
echo "Remaining codistech.live references (should be 0):"
grep -rn "codistech\.live" --include="*.yaml" --include="*.yml" --include="*.env*" --include="*.conf" --include="*.toml" . 2>/dev/null | grep -v ".git" | wc -l

echo ""
echo "=== Done! Review changes with: git diff ==="
echo "Then commit with: git add . && git commit -m 'Sanitize internal IPs and domains' && git push"
