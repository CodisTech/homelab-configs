# Inventory

Asset management system for tracking homelab hardware and software.

## Overview

Custom inventory application for cataloging and tracking homelab assets including servers, network equipment, and software licenses.

- **App** — Node.js web application
- **MySQL** — Database backend

## Why Custom?

Built custom to meet specific homelab tracking needs:

- Hardware inventory with specs and location
- Software license tracking
- Warranty and purchase date tracking
- Network equipment documentation
- Custom fields for homelab-specific data

## Architecture
```
┌─────────────┐     ┌─────────────┐
│  Inventory  │────▶│   MySQL     │
│    App      │     │     DB      │
│  (Node.js)  │     │             │
└─────────────┘     └─────────────┘
```

## NIST 800-53 Control Mapping

| Control Family | Controls Addressed | Implementation |
|----------------|-------------------|----------------|
| CM (Configuration Management) | CM-8 | Hardware/software inventory |
| PM (Program Management) | PM-5 | Asset tracking and documentation |

## Deployment
```bash
# Create secrets directory
mkdir -p secrets

# Generate passwords
openssl rand -base64 32 > secrets/mysql_root_password
openssl rand -base64 32 > secrets/mysql_password

# Start services
docker-compose up -d
```

## Configuration

### Secrets

This deployment uses Docker secrets instead of environment variables for enhanced security:

| Secret | Purpose |
|--------|---------|
| `mysql_root_password` | MySQL root user password |
| `mysql_password` | Application database user password |

### Ports

| Port | Service |
|------|---------|
| 5000 | Web interface |
| 3306 | MySQL (internal) |

## Security

- Docker secrets for credential management
- MySQL health checks before app startup
- Isolated network for database communication

## Resources

- [Docker Secrets](https://docs.docker.com/engine/swarm/secrets/)
