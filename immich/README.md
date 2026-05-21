# Immich

Self-hosted Google Photos replacement. Lives on VM 100 Docker; library on TrueNAS NFS.

- URL: https://photos.local.example.home (LAN; Traefik via cert-manager cloudflare resolver)
- Version: pinned via `IMMICH_VERSION` in `.env` (currently v2.7.5)
- Library: 1 TB NFS mount from Server C (`/storage/immich` → `/mnt/immich-library` → `/data` inside containers)
- Database: local SSD at `/home/serveradmin/docker_volumes/immich/postgres` (postgres performance unsuitable for NFS)
- Stack: server, machine-learning, redis (valkey), postgres (vectorchord)

## Operational

Live install path on VM 100: `/home/serveradmin/docker_volumes/immich/`
- `docker-compose.yml` (matches this dir)
- `.env` (mode 600; not in git — has DB_PASSWORD)
- `postgres/` (Postgres data dir)
- `model-cache` (named volume, ML models)

Memory limits per container — see project_vm100_pihole_grafana_fix.md history:
- server: 2 GB
- machine-learning: 3 GB
- postgres: 1 GB
- redis: 256 MB

## Pending for full at-home install

- Authentik OAuth wiring (requires admin UI access) — currently first-visit creates local admin
- Cloudflare Tunnel public hostname for mobile auto-upload off-WiFi
- Library import — copy/rsync existing photo collection into `/mnt/immich-library`

## Upgrades

- Snapshot TrueNAS `storage/immich` dataset before any major version bump
- Bump `IMMICH_VERSION` in `.env`, then `docker compose pull && docker compose up -d`
- Watch for breaking changes in Immich release notes — they're version-sensitive
