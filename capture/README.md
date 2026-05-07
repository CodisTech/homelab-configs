# Capture

Screenshot service for Checkmate uptime monitoring. Captures webpage screenshots for visual monitoring and change detection.

## Overview

Capture is a lightweight service that takes screenshots of monitored URLs, providing visual verification alongside uptime checks.

## Why Capture?

- Integrates directly with Checkmate monitoring
- Visual proof of service availability
- Detects UI changes that ping checks miss
- Lightweight Go-based service

## NIST 800-53 Control Mapping

| Control Family | Controls Addressed | Implementation |
|----------------|-------------------|----------------|
| CA (Assessment) | CA-7 | Continuous visual monitoring |
| SI (System Integrity) | SI-4 | Visual change detection |

## Deployment
```bash
# Copy environment template
cp .env.example .env

# Generate a secure API secret
echo "API_SECRET=$(openssl rand -hex 32)" > .env

# Start service
docker-compose up -d
```

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `API_SECRET` | Authentication key for API requests |

## Integration

Capture connects to Checkmate via the shared `checkmate_checkmate` network. Configure the capture URL in Checkmate settings.

## Resources

- [Checkmate GitHub](https://github.com/bluewave-labs/checkmate)
