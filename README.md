# Homelab Infrastructure as Code

> Production-grade, security-first homelab running 20+ self-hosted services across a segmented network with defense-in-depth architecture, GitOps workflow, and NIST 800-53 control mapping.

This is not a collection of tutorials. This is a living infrastructure that I operate, monitor, and secure daily — applying the same principles I used managing cybersecurity operations aboard USS Nimitz (CVN-68) to a self-hosted environment.

## Why This Exists

Enterprise security concepts do not require enterprise budgets. This homelab demonstrates that defense-in-depth, zero-trust access, centralized monitoring, and compliance-ready infrastructure can be built with open-source tools and thoughtful architecture.

Every configuration in this repository is production — these are the actual files running my infrastructure, version-controlled and continuously maintained.

## Architecture

```
Internet
    │
    ▼
┌──────────────────────────────────────────────────────┐
│                   Edge Layer                          │
│  Cloudflare ──▶ Traefik ──▶ CrowdSec ──▶ Authentik  │
│  (CDN/WAF)     (Reverse     (Threat      (SSO/MFA)  │
│                 Proxy)       Detection)              │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────┐
│              Network Segmentation                     │
│                                                       │
│  VLAN 10 ─ Management    VLAN 30 ─ IoT/Smart Home    │
│  VLAN 20 ─ Services      VLAN 40 ─ Business (CRL)   │
│                                                       │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────┐
│              Security Monitoring                      │
│                                                       │
│  Wazuh SIEM ─── Prometheus/Grafana ─── Pi-hole DNS   │
│  (2,337 vulns    (Metrics &             (DNS          │
│   triaged)        Dashboards)            Filtering)   │
│                                                       │
└──────────────────────┬───────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────┐
│              Hypervisors & Storage                     │
│                                                       │
│  Proxmox VE (256GB + 128GB RAM)  ─── Unraid (80TB)  │
│                                                       │
└──────────────────────────────────────────────────────┘
```

## Services

### Security and Access Control

| Service | Purpose | Key Detail |
|---------|---------|------------|
| [Wazuh](wazuh/) | SIEM, log analysis, FIM, vulnerability detection | 2,337 vulnerabilities triaged, NIST 800-53 mapped |
| [Traefik](traefik/) | Reverse proxy, automatic TLS, request routing | Integrated with CrowdSec and Cloudflare |
| [Authentik](authentik/) | Identity provider, SSO, MFA enforcement | Zero-trust access for all services |
| [Pi-hole](pihole/) | DNS filtering and ad blocking | Dual-instance for redundancy |

### Monitoring and Observability

| Service | Purpose | Key Detail |
|---------|---------|------------|
| [Prometheus/Grafana](opensense-monitoring/) | Metrics collection and visualization | Custom dashboards for infrastructure health |
| [Loki/Promtail](opensense-monitoring/) | Log aggregation and search | Complements Wazuh for operational logs |
| [Checkmate](checkmate/) | Uptime monitoring | Service availability tracking |
| [Netdata](monitoring/) | Real-time system metrics | Per-host performance monitoring |

### Automation and DevOps

| Service | Purpose | Key Detail |
|---------|---------|------------|
| [n8n](n8n/) | Workflow automation | Content publishing, alerting, business processes |
| [Renovate](renovate/) | Automated dependency updates | Creates PRs for Docker image updates |
| [Diun](diun/) | Container update notifications | Telegram alerts for new image versions |
| [Gitea](gitea/) | Self-hosted Git | Internal source of truth for all configs |

### Applications

| Service | Purpose | Key Detail |
|---------|---------|------------|
| [Nextcloud](nextcloud/) | File sync and collaboration | Self-hosted alternative to Google Drive |
| [Home Assistant](homeassistant/) | Smart home automation | Matter/Thread architecture with voice control |
| [Firefly III](firefly-iii/) | Financial management | Self-hosted accounting with Profit First methodology |
| [Media](media/) | Plex, Emby media servers | Centralized media management |

## Security Features

**Zero-trust access** — Every service sits behind Authentik SSO with MFA enforcement. No service is directly exposed without authentication.

**TLS everywhere** — Traefik automatically provisions and renews certificates via Cloudflare DNS challenge. All internal and external traffic is encrypted.

**Behavioral threat detection** — CrowdSec analyzes access patterns and automatically blocks malicious IPs based on community threat intelligence.

**Centralized SIEM** — All logs ship to Wazuh for correlation, alerting, and compliance reporting. File integrity monitoring detects unauthorized changes.

**Network segmentation** — Isolated VLANs with firewall rules controlling inter-segment traffic. IoT devices cannot reach management infrastructure.

**Secrets management** — Environment variables for all sensitive configuration. `.env.example` templates provided, actual secrets never committed to git.

**Automated patching workflow** — Diun detects available container updates, Renovate creates pull requests, human reviews and merges, production pulls updated images.

## GitOps Workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Diun     │────▶│  Telegram   │     │  Renovate   │
│  (8 AM)     │     │   Alert     │     │  (9 AM)     │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                        ┌──────▼──────┐
                                        │   Gitea PR  │
                                        └──────┬──────┘
                                               │
                                        ┌──────▼──────┐
                                        │   Review    │
                                        │   & Merge   │
                                        └──────┬──────┘
                                               │
                                        ┌──────▼──────┐
                                        │  Production │
                                        │  Deploy     │
                                        └─────────────┘
```

Every infrastructure change is tracked, reviewed, and reversible.

## Quick Start

```bash
git clone https://github.com/CodisTech/homelab-configs.git
cd homelab-configs/<service>
cp .env.example .env
# Edit .env with your values
docker-compose up -d
```

Each service directory contains its own README with specific deployment instructions, configuration details, and lessons learned.

## Related Projects

- [Policy-as-Code Framework](https://github.com/CodisTech/policy-as-code) — Compliance policies defined as code using OPA, InSpec, and Sentinel
- [CyberReadyLabs](https://cyberreadylabs.com) — Cybersecurity consulting built on this infrastructure

## License

[MIT](LICENSE)
