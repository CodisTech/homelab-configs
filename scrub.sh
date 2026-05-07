#!/bin/bash
# =============================================================================
# scrub.sh — sanitize homelab-configs for the public GitHub mirror.
# =============================================================================
# Inverts the rules the legacy .githooks/pre-push hook used to enforce. After
# the architecture flip, this repo holds REAL values; scrub.sh produces the
# sanitized snapshot that gets pushed to github.com/CodisTech/homelab-configs.
#
# Usage:
#   ./scrub.sh                # writes sanitized copy to ./_public/
#   ./scrub.sh --in-place     # rewrites the working tree itself (DANGEROUS —
#                               only use on a throwaway clone for mirror push)
#   ./scrub.sh --check        # exits non-zero if any tracked file in the
#                               working tree still contains REAL values that
#                               would leak. Useful as a CI gate.
#
# Replacement rules (applied to all tracked files except .git, _public,
# *.png/*.jpg/*.pdf/*.gz/*.zip/*.tar.* binaries):
#   local.example.home      -> local.example.home
#   example.home            -> example.home
#   192.168.<X>.<Y>           -> 10.0.<X>.<Y>
#
# Adding more patterns: edit SED_RULES below. Keep them deterministic and
# round-trippable in spirit (don't lose information needed for readers to
# understand the structure of the config).
# =============================================================================

set -euo pipefail

MODE="copy"
for arg in "$@"; do
    case "$arg" in
        --in-place) MODE="in-place" ;;
        --check)    MODE="check" ;;
        -h|--help)  sed -n '2,30p' "$0"; exit 0 ;;
        *)          echo "Unknown arg: $arg" >&2; exit 1 ;;
    esac
done

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
OUTPUT_DIR="$REPO_ROOT/_public"

# Order matters — apply more-specific replacements before more-general.
# "local.example.home" must be rewritten before the bare "example.home"
# rule fires so we get "local.example.home" not "local.example.home".
SED_RULES=(
    -e 's/\blocal\.codistech\.live\b/local.example.home/g'
    -e 's/\bcodistech\.live\b/example.home/g'
    -e 's/\b192\.168\.\([0-9]\+\)\.\([0-9]\+\)\b/10.0.\1.\2/g'
)

# Files to skip entirely (binaries, build outputs).
should_skip() {
    case "$1" in
        ./_public/*|./.git/*) return 0 ;;
        *.png|*.jpg|*.jpeg|*.gif|*.pdf|*.ico) return 0 ;;
        *.gz|*.zip|*.tar.gz|*.tgz|*.bz2|*.xz) return 0 ;;
        *.bin|*.dat) return 0 ;;
    esac
    return 1
}

# Patterns that constitute a leak — search for these to exit non-zero in
# --check mode.
LEAK_PATTERNS='(\bcodistech\.live\b|\b192\.168\.[0-9]+\.[0-9]+\b)'

case "$MODE" in
    check)
        echo "[scrub] --check: scanning for unsanitized values..."
        cd "$REPO_ROOT"
        violations=$(git ls-files | while read -r f; do
            should_skip "./$f" && continue
            grep -HnE "$LEAK_PATTERNS" "$f" 2>/dev/null || true
        done)
        if [ -n "$violations" ]; then
            echo "[scrub] LEAK PATTERNS FOUND in tracked files:"
            echo "$violations" | head -50
            echo "[scrub] Run scrub.sh (without --check) before pushing to public mirror."
            exit 1
        fi
        echo "[scrub] clean."
        exit 0
        ;;
    copy)
        echo "[scrub] sanitizing tracked files into $OUTPUT_DIR"
        rm -rf "$OUTPUT_DIR"
        mkdir -p "$OUTPUT_DIR"
        cd "$REPO_ROOT"
        git ls-files | while read -r f; do
            local_dst="$OUTPUT_DIR/$f"
            mkdir -p "$(dirname "$local_dst")"
            if should_skip "./$f"; then
                cp -p "$f" "$local_dst"
            else
                sed "${SED_RULES[@]}" "$f" > "$local_dst"
                chmod --reference="$f" "$local_dst" 2>/dev/null || true
            fi
        done
        echo "[scrub] done. $OUTPUT_DIR contains the sanitized snapshot."
        echo "[scrub] Verify: grep -rE 'codistech\\.live|192\\.168' $OUTPUT_DIR | head"
        ;;
    in-place)
        echo "[scrub] rewriting working tree IN PLACE"
        echo "[scrub] press ctrl-c within 3 seconds to abort..."
        sleep 3
        cd "$REPO_ROOT"
        git ls-files | while read -r f; do
            should_skip "./$f" && continue
            sed -i "${SED_RULES[@]}" "$f"
        done
        echo "[scrub] done. Inspect 'git diff' before committing."
        ;;
esac
