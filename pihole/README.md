# Pi-hole

Network-wide ad blocking and DNS filtering.

## Overview

Pi-hole provides DNS-level ad blocking for the entire network. This is pihole2 — a secondary DNS server for redundancy (pihole1 runs on separate hardware).

## Why Pi-hole?

- Network-wide blocking — No per-device configuration
- Reduced bandwidth — Ads blocked before download
- Improved privacy — Blocks tracking domains
- Custom DNS — Internal domain resolution
- Statistics — Visibility into DNS queries

## Architecture
```
┌─────────────┐     ┌─────────────┐
│   Clients   │────▶│  Pi-hole 1  │ (primary)
│             │     │ 10.0.0.55│
└─────────────┘     └─────────────┘
       │
       │            ┌─────────────┐
       └───────────▶│  Pi-hole 2  │ (secondary)
                    │ (this one)  │
                    └─────────────┘
                           │
                    ┌──────▼──────┐
                    │  Quad9 DNS  │
                    │  9.9.9.9    │
                    └─────────────┘
```

## NIST 800-53 Control Mapping

| Control Family | Controls Addressed | Implementation |
|----------------|-------------------|----------------|
| SC (System & Communications) | SC-7, SC-20 | DNS filtering, malicious domain blocking |
| SI (System Integrity) | SI-3, SI-4 | Malware domain blocking, query logging |
| AU (Audit) | AU-3 | DNS query logging |

## Deployment
```bash
cp .env.example .env
nano .env  # Set WEBPASSWORD

docker-compose up -d
```

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `WEBPASSWORD` | Admin dashboard password |

### Upstream DNS

Uses Quad9 (9.9.9.9, 149.112.112.112) for:
- Malware domain blocking
- Privacy-focused (no logging)
- DNSSEC validation

### Ports

| Port | Purpose |
|------|---------|
| 53 | DNS (host network mode) |
| 8080 | Web admin interface |

## Resources

- [Pi-hole Documentation](https://docs.pi-hole.net/)
- [Quad9](https://www.quad9.net/)
