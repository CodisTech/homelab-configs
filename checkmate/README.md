# Checkmate

Uptime monitoring and performance tracking for homelab services.

## Overview

Checkmate provides continuous uptime monitoring with alerting, performance metrics, and visual screenshots via the Capture service. Components include:

- **Client** — Web dashboard for viewing status and metrics
- **Server** — API backend and monitoring engine
- **MongoDB** — Data persistence
- **Redis** — Caching and job queue

## Why Checkmate?

Selected over alternatives (Uptime Kuma, Statping, Healthchecks.io) for:

- Clean, modern UI
- Google PageSpeed integration for performance metrics
- Screenshot capture support
- Self-hosted with no external dependencies
- Active open-source development

## Architecture
```
┌─────────────┐     ┌─────────────┐
│   Traefik   │────▶│   Client    │
└─────────────┘     └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Server    │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │ MongoDB  │ │  Redis   │ │ Capture  │
        └──────────┘ └──────────┘ └──────────┘
```

## NIST 800-53 Control Mapping

| Control Family | Controls Addressed | Implementation |
|----------------|-------------------|----------------|
| CA (Assessment) | CA-7 | Continuous monitoring of service availability |
| IR (Incident Response) | IR-4, IR-6 | Alerting on service outages |
| SI (System Integrity) | SI-4 | Performance monitoring and anomaly detection |

## Deployment
```bash
# Copy environment template
cp .env.example .env

# Add your PageSpeed API key (optional, for performance metrics)
nano .env

# Start services
docker-compose up -d
```

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `PAGESPEED_API_KEY` | Google PageSpeed API key for performance metrics (optional) |

### Getting a PageSpeed API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project or select existing
3. Enable PageSpeed Insights API
4. Create credentials → API key

## Integration

Checkmate integrates with [Capture](../capture/) for visual monitoring. Both services share the `checkmate` network.

## Resources

- [Checkmate GitHub](https://github.com/bluewave-labs/checkmate)
- [PageSpeed API](https://developers.google.com/speed/docs/insights/v5/get-started)
