# n8n

Workflow automation platform for connecting services and automating tasks.

## Overview

n8n is a self-hosted workflow automation tool that connects apps and services. This deployment includes Cloudflare Tunnel for secure external webhook access.

- **n8n** — Workflow engine and editor
- **Cloudflared** — Secure tunnel for external webhooks

## Why n8n?

Selected over alternatives (Zapier, Make, Node-RED) for:

- Self-hosted — Full data control, no cloud dependency
- No execution limits — Unlike SaaS alternatives
- 400+ integrations — Wide service support
- Visual editor — Easy workflow building
- Code when needed — JavaScript/Python support

## Architecture
```
┌─────────────────┐     ┌─────────────┐
│    Traefik      │────▶│     n8n     │
│ (internal)      │     │  (editor)   │
└─────────────────┘     └──────┬──────┘
                               │
┌─────────────────┐            │
│  Cloudflare     │────────────┘
│  Tunnel         │  (external webhooks)
└─────────────────┘
```

## NIST 800-53 Control Mapping

| Control Family | Controls Addressed | Implementation |
|----------------|-------------------|----------------|
| SA (System & Services Acquisition) | SA-9 | Secure external service integration |
| AU (Audit) | AU-2 | Workflow execution logging |
| SC (System & Communications) | SC-8 | Encrypted tunnel for webhooks |

## Deployment
```bash
cp .env.example .env

# Add your Cloudflare Tunnel token
nano .env

docker-compose up -d
```

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `CF_TUNNEL_TOKEN` | Cloudflare Tunnel token for external access |

### URLs

| URL | Purpose |
|-----|---------|
| `n8n.local.codistech.live` | Internal editor access |
| `n8n-webhook.codistech.live` | External webhook endpoint |

## Use Cases

- LinkedIn content automation from README updates
- Calendar sync and notifications
- Infrastructure alerting
- Data transformation pipelines
- API integrations

## Resources

- [n8n Documentation](https://docs.n8n.io/)
- [n8n Community](https://community.n8n.io/)
- [Cloudflare Tunnels](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
