# Homelab Configs

Infrastructure as Code for a security-focused homelab environment. This repository contains Docker Compose configurations, custom rules, and documentation for self-hosted services with an emphasis on defense-in-depth principles.

## About

This homelab serves as both a production environment and a learning platform for implementing enterprise security concepts at home scale. Configurations follow security best practices and map to NIST 800-53 controls where applicable.

## Services

| Service | Purpose | Docs |
|---------|---------|------|
| [Wazuh](wazuh/) | SIEM, log analysis, FIM | [README](wazuh/README.md) |
| [Traefik](traefik/) | Reverse proxy, TLS, CrowdSec | [README](traefik/README.md) |
| [Authentik](authentik/) | Identity provider, SSO, MFA | [README](authentik/README.md) |
| [Monitoring](opensense-monitoring/) | Prometheus, Grafana, Loki | [README](opensense-monitoring/README.md) |
| [n8n](n8n/) | Workflow automation | [README](n8n/README.md) |
| [Home Assistant](homeassistant/) | Home automation, voice control | [README](homeassistant/README.md) |
| [Gitea](gitea/) | Self-hosted Git | [README](gitea/README.md) |
| [Pi-hole](pihole/) | DNS filtering | [README](pihole/README.md) |
| [Portainer](portainer/) | Container management | [README](portainer/README.md) |
| [Checkmate](checkmate/) | Uptime monitoring | [README](checkmate/README.md) |
| [Capture](capture/) | Screenshot service | [README](capture/README.md) |
| [Media](media/) | Plex, Emby | [README](media/README.md) |
| [Heimdall](heimdall/) | App dashboard | [README](heimdall/README.md) |
| [Nginx](nginx/) | Web server | [README](nginx/README.md) |
| [Inventory](inventory/) | Asset management | [README](inventory/README.md) |
| [Games](games/) | Minecraft server | [README](games/README.md) |
| [Netdata](monitoring/) | Real-time metrics | [README](monitoring/README.md) |
| [Diun](diun/) | Container update notifications | [README](diun/README.md) |
| [Renovate](renovate/) | Automated dependency PRs | [README](renovate/README.md) |

## Architecture
```
Internet
    │
    ▼
┌──────────┐     ┌───────────┐     ┌───────────┐
│ Traefik  │────▶│ CrowdSec  │────▶│ Authentik │
└────┬─────┘     └───────────┘     └───────────┘
     │
     ├──▶ Wazuh (SIEM)
     ├──▶ Grafana (Monitoring)
     ├──▶ Gitea (Git)
     ├──▶ n8n (Automation)
     ├──▶ Home Assistant (IoT)
     ├──▶ Proxmox (Virtualization)
     ├──▶ Unraid (Storage)
     ├──▶ pfSense (Firewall)
     ├──▶ Unifi (Network)
     ├──▶ Nextcloud (Files)
     ├──▶ Pi-hole x2 (DNS)
     ├──▶ Portainer (Containers)
     ├──▶ Heimdall (Dashboard)
     └──▶ Media Services
```

## Security Features

- **Zero-trust access** — Services behind Authentik SSO
- **TLS everywhere** — Automatic certificates via Traefik + Cloudflare
- **Threat detection** — CrowdSec behavioral analysis and IP blocking
- **Centralized logging** — Logs shipped to Wazuh SIEM and Loki
- **Network segmentation** — Isolated Docker networks per service group
- **Secrets management** — Environment variables, never committed to git

## Quick Start
```bash
# Clone the repo
git clone https://github.com/codistech/homelab-configs.git
cd homelab-configs

# Deploy a service
cd <service>
cp .env.example .env
# Edit .env with your values
docker-compose up -d
```

## License

[MIT](LICENSE)
