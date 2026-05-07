# Portainer

Docker container management web interface.

## Overview

Portainer provides a GUI for managing Docker containers, images, volumes, and networks. Protected by Authentik SSO.

## Why Portainer?

- Visual container management
- Stack deployment from compose files
- Resource monitoring
- Multi-environment support
- Template library

## NIST 800-53 Control Mapping

| Control Family | Controls Addressed | Implementation |
|----------------|-------------------|----------------|
| CM (Configuration Management) | CM-2, CM-3 | Container configuration management |
| AC (Access Control) | AC-2, AC-3 | SSO via Authentik, role-based access |

## Deployment
```bash
docker-compose up -d

# First access: create admin account
# Subsequent access: via Authentik SSO
```

## Security

- `no-new-privileges` — Prevents privilege escalation
- Docker socket mounted read-only
- Authentik SSO required for access

## Resources

- [Portainer Documentation](https://docs.portainer.io/)
