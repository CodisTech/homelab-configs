# Homelab Configs

Infrastructure as Code for a security-focused homelab environment. This repository contains Docker Compose configurations, custom rules, and documentation for self-hosted services with an emphasis on defense-in-depth principles.

## About

This homelab serves as both a production environment and a learning platform for implementing enterprise security concepts at home scale. Configurations follow security best practices and map to NIST 800-53 controls where applicable.

## Services

| Service | Purpose | Documentation |
|---------|---------|---------------|
| **Wazuh** | SIEM, log analysis, file integrity monitoring | [README](wazuh/README.md) |
| **Traefik** | Reverse proxy with automatic TLS | [README](traefik/README.md) |
| **Authentik** | Identity provider, SSO, MFA | [README](authentik/README.md) |
| **n8n** | Workflow automation | [README](n8n/README.md) |
| **Monitoring** | Prometheus, Grafana, Loki, Alertmanager | [README](monitoring/README.md) |
| **OPNsense Monitoring** | Firewall metrics and logging | [README](opensense-monitoring/README.md) |
| **Gitea** | Self-hosted Git server | [README](gitea/README.md) |
| **Pi-hole** | DNS filtering, ad blocking | [README](pihole/README.md) |
| **Home Assistant** | Home automation, IoT management | [README](homeassistant/README.md) |
| **Portainer** | Docker container management | [README](portainer/README.md) |
| **Heimdall** | Application dashboard | [README](heimdall/README.md) |
| **Nginx** | Web server | [README](nginx/README.md) |
| **Media** | Plex, media services | [README](media/README.md) |
| **Games** | Game servers | [README](games/README.md) |
| **Capture** | Packet capture, network analysis | [README](capture/README.md) |
| **Checkmate** | Uptime monitoring | [README](checkmate/README.md) |
| **Inventory** | Asset management | [README](inventory/README.md) |

## Architecture
```
Internet
    │
    ▼
┌──────────┐     ┌───────────┐
│ Traefik  │────▶│ Authentik │ (SSO/MFA)
└────┬─────┘     └───────────┘
     │
     ├──▶ Wazuh (SIEM)
     ├──▶ Grafana (Monitoring)
     ├──▶ Gitea (Git)
     ├──▶ n8n (Automation)
     ├──▶ Home Assistant (IoT)
     └──▶ Media Services
```

## Security Features

- **Zero-trust access** — Services behind Authentik SSO
- **TLS everywhere** — Automatic certificates via Traefik + Cloudflare
- **Centralized logging** — Logs shipped to Wazuh SIEM
- **Network segmentation** — Isolated Docker networks per service group
- **Firewall monitoring** — OPNsense metrics and alerts
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

## Structure
```
├── authentik/              # Identity provider
├── capture/                # Packet capture
├── checkmate/              # Uptime monitoring
├── games/                  # Game servers
├── gitea/                  # Git server
├── heimdall/               # App dashboard
├── homeassistant/          # Home automation
├── inventory/              # Asset management
├── media/                  # Plex, media services
├── monitoring/             # Prometheus, Grafana, Loki
├── n8n/                    # Workflow automation
├── nginx/                  # Web server
├── opensense-monitoring/   # Firewall monitoring
├── pihole/                 # DNS filtering
├── portainer/              # Container management
├── traefik/                # Reverse proxy
└── wazuh/                  # SIEM
```

## License

MIT