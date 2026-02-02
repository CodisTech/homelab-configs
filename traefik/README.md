# Traefik

Reverse proxy with automatic TLS, CrowdSec security, and Authentik SSO integration.

## Overview

Traefik serves as the single entry point for all homelab services, providing:

- **Traefik** — Reverse proxy and load balancer
- **CrowdSec** — Threat detection and IP blocking
- **CrowdSec Bouncer** — Traefik middleware for blocking malicious IPs
- **Promtail** — Log shipping to Loki

## Why Traefik?

Selected over alternatives (Nginx Proxy Manager, Caddy, HAProxy) for:

- Native Docker integration with labels
- Automatic Let's Encrypt/Cloudflare certificates
- Dynamic configuration without restarts
- Built-in dashboard
- Middleware ecosystem
- CrowdSec integration

## Architecture
```
                    Internet
                        │
                        ▼
┌──────────────────────────────────────────────────┐
│                    Traefik                        │
│              (reverse proxy)                      │
└───────────┬──────────────────────┬───────────────┘
            │                      │
     ┌──────▼──────┐        ┌──────▼──────┐
     │  CrowdSec   │        │  Authentik  │
     │  Bouncer    │        │  (SSO)      │
     └──────┬──────┘        └─────────────┘
            │
     ┌──────▼──────┐
     │  CrowdSec   │
     │  (detection)│
     └─────────────┘
            │
     ┌──────▼──────┐
     │  Promtail   │───▶ Loki
     │  (logs)     │
     └─────────────┘
```

## NIST 800-53 Control Mapping

| Control Family | Controls Addressed | Implementation |
|----------------|-------------------|----------------|
| SC (System & Communications) | SC-7, SC-8, SC-13 | TLS termination, encrypted transit |
| AC (Access Control) | AC-3, AC-17 | Authentik SSO, remote access control |
| SI (System Integrity) | SI-3, SI-4 | CrowdSec threat detection |
| AU (Audit) | AU-2, AU-3 | Access logging via Promtail |

## Security Stack

### CrowdSec

Behavioral detection engine that:
- Parses Traefik access logs
- Detects attacks (brute force, scanners, CVE exploits)
- Shares threat intelligence with community
- Blocks malicious IPs via bouncer

Collections enabled:
- `crowdsecurity/traefik`
- `crowdsecurity/http-cve`
- `crowdsecurity/sshd`
- `crowdsecurity/linux`

### Middlewares

| Middleware | Purpose |
|------------|---------|
| `authentik` | SSO for protected services |
| `crowdsec-bouncer` | IP blocking |
| `default-security-headers` | Security headers |
| `https-redirectscheme` | HTTP to HTTPS redirect |

## Deployment
```bash
# Create secrets
echo "your-cloudflare-token" > cf-token
chmod 600 cf-token

# Create empty acme.json
touch acme.json
chmod 600 acme.json

# Copy environment template
cp .env.example .env
nano .env

# Start services
docker-compose up -d
```

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `TRAEFIK_DASHBOARD_CREDENTIALS` | htpasswd hash for dashboard |
| `CROWDSEC_BOUNCER_API_KEY` | API key for bouncer |

### Generate Dashboard Credentials
```bash
htpasswd -nb admin yourpassword
```

### Files

| File | Purpose |
|------|---------|
| `traefik.yaml` | Static configuration |
| `config.yaml` | Dynamic configuration (routes, middlewares) |
| `cf-token` | Cloudflare API token (secret) |
| `acme.json` | Certificate storage |
| `promtail-config.yaml` | Log shipping config |

### Ports

| Port | Purpose |
|------|---------|
| 80 | HTTP (redirects to HTTPS) |
| 443 | HTTPS |
| 8082 | Metrics (Prometheus) |

## Resources

- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [CrowdSec Documentation](https://docs.crowdsec.net/)
- [Cloudflare DNS Challenge](https://go-acme.github.io/lego/dns/cloudflare/)
