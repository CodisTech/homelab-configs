# Monitoring Stack

Full observability stack for metrics, logs, and alerting.

## Overview

Comprehensive monitoring solution providing real-time visibility into all homelab infrastructure:

- **Prometheus** — Metrics collection and storage
- **Grafana** — Visualization and dashboards
- **Loki** — Log aggregation
- **Alertmanager** — Alert routing and notifications
- **Node Exporter** — Host system metrics
- **cAdvisor** — Container metrics
- **Blackbox Exporter** — Endpoint probing
- **Pi-hole Exporter** — DNS metrics
- **PVE Exporter** — Proxmox metrics

## Architecture
```
┌─────────────────────────────────────────────────────────┐
│                       Grafana                            │
│                    (dashboards)                          │
└─────────┬─────────────────┬─────────────────────────────┘
          │                 │
    ┌─────▼─────┐     ┌─────▼─────┐
    │Prometheus │     │   Loki    │
    │ (metrics) │     │  (logs)   │
    └─────┬─────┘     └───────────┘
          │
    ┌─────┴─────────────────┐
    │      Exporters        │
    ├───────────────────────┤
    │ • Node Exporter       │
    │ • cAdvisor            │
    │ • Blackbox            │
    │ • Pi-hole Exporter    │
    │ • PVE Exporter        │
    └───────────────────────┘
          │
    ┌─────▼─────┐
    │Alertmanager│
    └───────────┘
```

## NIST 800-53 Control Mapping

| Control Family | Controls Addressed | Implementation |
|----------------|-------------------|----------------|
| AU (Audit) | AU-2, AU-3, AU-6, AU-12 | Centralized logging and monitoring |
| SI (System Integrity) | SI-4 | Continuous system monitoring |
| IR (Incident Response) | IR-4, IR-5 | Alerting and notification |
| CA (Assessment) | CA-7 | Continuous monitoring dashboards |

## Deployment
```bash
cp .env.example .env
nano .env
docker-compose up -d
```

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `PIHOLE_PASSWORD` | Pi-hole admin password for API access |
| `PVE_USER` | Proxmox API user (e.g., root@pam) |
| `PVE_TOKEN_NAME` | Proxmox API token name |
| `PVE_TOKEN_VALUE` | Proxmox API token value |

### Ports

| Service | Port |
|---------|------|
| Prometheus | 9090 |
| Grafana | 3000 |
| Loki | 3100 |
| Alertmanager | 9093 |
| Node Exporter | 9100 |
| cAdvisor | 8081 |
| Blackbox | 9115 |
| Pi-hole Exporter | 9617 |
| PVE Exporter | 9221 |

### Retention

- Prometheus: 15 days metric retention

## Resources

- [Prometheus Docs](https://prometheus.io/docs/)
- [Grafana Docs](https://grafana.com/docs/)
- [Loki Docs](https://grafana.com/docs/loki/)
