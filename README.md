# Homelab Configs

Infrastructure as Code for Codistech Homelab.

## Structure
```
├── monitoring/          # Prometheus, Grafana, Loki, Alertmanager
│   ├── prometheus/      # Prometheus config and alert rules
│   ├── alertmanager/    # Alertmanager config
│   └── loki/            # Loki config
├── traefik/             # Traefik reverse proxy + CrowdSec
└── gitea/               # Gitea git server
```

## Services

| Service | URL | Purpose |
|---------|-----|---------|
| Grafana | grafana.local.codistech.live | Dashboards & visualization |
| Prometheus | prometheus.local.codistech.live | Metrics collection |
| Gitea | git.local.codistech.live | Private Git repos |
| Traefik | traefik.local.codistech.live | Reverse proxy |

## Secrets

Secrets are stored in `.env` files (not committed). Template:
```bash
# monitoring/.env
PIHOLE_PASSWORD=
PVE_USER=
PVE_TOKEN_NAME=
PVE_TOKEN_VALUE=
```

## Deployment
```bash
cd <service>
docker-compose up -d
```
