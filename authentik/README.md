# Authentik

Identity Provider (IdP) for Single Sign-On (SSO) and Multi-Factor Authentication (MFA) across homelab services.

## Overview

Authentik provides centralized authentication and authorization, eliminating the need for separate credentials on each service. This deployment includes:

- **Server** — Core authentication service
- **Worker** — Background task processing
- **PostgreSQL** — User and configuration database
- **Redis** — Session cache and task queue

## Why Authentik?

Selected over alternatives (Keycloak, Authelia, Dex) for:

- Modern, clean UI for both admin and end users
- Built-in support for SAML, OAuth2, OIDC, LDAP, and proxy authentication
- Customizable authentication flows
- Strong MFA support (TOTP, WebAuthn, Duo)
- Active development and community

## Architecture
```
┌─────────────┐     ┌─────────────┐
│   Traefik   │────▶│  Authentik  │
│  (proxy)    │     │  (server)   │
└─────────────┘     └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │PostgreSQL│ │  Redis   │ │  Worker  │
        └──────────┘ └──────────┘ └──────────┘
```

## NIST 800-53 Control Mapping

| Control Family | Controls Addressed | Implementation |
|----------------|-------------------|----------------|
| IA (Identification & Authentication) | IA-2, IA-5, IA-8 | Centralized identity, MFA enforcement |
| AC (Access Control) | AC-2, AC-3, AC-6 | Role-based access, least privilege |
| AU (Audit) | AU-2, AU-3 | Authentication logging, session tracking |

## Protected Services

| Service | Auth Method |
|---------|-------------|
| Portainer | Forward Auth |
| Prometheus | Forward Auth |
| Traefik Dashboard | Forward Auth |

## Deployment
```bash
# Copy environment template
cp .env.example .env

# Edit with your values
nano .env

# Start services
docker-compose up -d

# Initial setup at https://auth.yourdomain.com/if/flow/initial-setup/
```

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `PG_PASS` | PostgreSQL database password |
| `AUTHENTIK_SECRET_KEY` | Secret key for signing tokens |
| `AUTHENTIK_EMAIL__HOST` | SMTP server hostname |
| `AUTHENTIK_EMAIL__PORT` | SMTP port (587 for TLS) |
| `AUTHENTIK_EMAIL__USERNAME` | SMTP username |
| `AUTHENTIK_EMAIL__PASSWORD` | SMTP password or app password |
| `AUTHENTIK_EMAIL__USE_TLS` | Enable TLS for email |
| `AUTHENTIK_EMAIL__FROM` | From address for emails |

### Traefik Integration

Authentik integrates with Traefik via forward authentication middleware:
```yaml
middlewares:
  authentik:
    forwardAuth:
      address: http://authentik-server:9000/outpost.goauthentik.io/auth/traefik
      trustForwardHeader: true
      authResponseHeaders:
        - X-authentik-username
        - X-authentik-groups
        - X-authentik-email
```

Apply to any route to require authentication:
```yaml
routers:
  my-service:
    middlewares:
      - authentik
```

## Resources

- [Authentik Documentation](https://goauthentik.io/docs/)
- [Traefik Forward Auth](https://goauthentik.io/integrations/services/traefik/)
