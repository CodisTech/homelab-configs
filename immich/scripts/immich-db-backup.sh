#!/bin/bash
# immich-db-backup.sh — daily pg_dumpall of Immich postgres on VM 100.
#
# Writes to /mnt/immich-library/db-backups/ which is the NFS share to Server C's
# storage/immich dataset. That same path is picked up by restic-backup.sh on
# k3s-control (mounted RO at /storage/immich/db-backups/) so the DB and photo
# library go to Backblaze B2 in the same coherent snapshot.
#
# Container: immich_postgres (Immich's bundled pgvector postgres).
# Retention: 7 daily dumps locally; restic keeps its own retention chain.

set -euo pipefail

DEST="/mnt/immich-library/db-backups"
CONTAINER="immich_postgres"
RETENTION_DAYS=7
LOG_TAG="immich-db-backup"

log() {
    logger -t "$LOG_TAG" "$1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Mount sanity — abort if NFS isn't actually attached (don't dump to local disk).
if ! mountpoint -q /mnt/immich-library; then
    log "ERROR: /mnt/immich-library is not a mountpoint; aborting"
    exit 1
fi

mkdir -p "$DEST"
NOW=$(date +%Y%m%d-%H%M%S)
OUT="$DEST/immich-pgdumpall-$NOW.sql.gz"

log "Dumping $CONTAINER → $OUT"

if ! docker exec "$CONTAINER" pg_dumpall -U postgres | gzip -9 > "$OUT.tmp"; then
    log "ERROR: pg_dumpall failed; removing partial file"
    rm -f "$OUT.tmp"
    exit 1
fi
mv "$OUT.tmp" "$OUT"

SIZE=$(stat -c %s "$OUT" 2>/dev/null || echo 0)
log "Wrote $OUT ($(numfmt --to=iec "$SIZE" 2>/dev/null || echo "$SIZE bytes"))"

# Prune older dumps locally (restic keeps its own retention chain)
DELETED=$(find "$DEST" -name "immich-pgdumpall-*.sql.gz" -mtime +"$RETENTION_DAYS" -print -delete 2>/dev/null | wc -l)
[ "$DELETED" -gt 0 ] && log "Pruned $DELETED dumps older than ${RETENTION_DAYS}d"

log "Done"
