# Gitea

Self-hosted Git server for private repositories and version control.

## Overview

Gitea is a lightweight, self-hosted Git service providing repository hosting, issue tracking, and CI/CD capabilities. This is the source of truth for all homelab configurations, mirrored to GitHub for public portfolio visibility.

## Why Gitea?

Selected over alternatives (GitLab, Gogs, Forgejo) for:

- Lightweight — minimal resource usage compared to GitLab
- Feature-rich — issues, PRs, wikis, actions
- Active development and community
- Easy migration to/from GitHub
- Built-in mirroring support

## Architecture
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Traefik   │────▶│   Gitea     │────▶│   GitHub    │
│   (proxy)   │     │  (primary)  │     │  (mirror)   │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                    ┌──────▼──────┐
                    │   SQLite    │
                    └─────────────┘
```

## NIST 800-53 Control Mapping

| Control Family | Controls Addressed | Implementation |
|----------------|-------------------|----------------|
| CM (Configuration Management) | CM-2, CM-3 | Version-controlled configurations |
| AU (Audit) | AU-3, AU-6 | Commit history, change tracking |
| AC (Access Control) | AC-2, AC-3 | Repository permissions, SSH keys |

## Deployment
```bash
# Start service
docker-compose up -d

# Access at https://git.yourdomain.com
# First user registered becomes admin
```

## Configuration

### Ports

| Port | Purpose |
|------|---------|
| 3001 | Web interface (proxied via Traefik) |
| 2222 | SSH for git operations |

### SSH Clone
```bash
git clone ssh://git@git.local.codistech.live:2222/user/repo.git
```

### Push Mirroring to GitHub

1. Create GitHub Personal Access Token
2. In Gitea: Repository Settings → Mirror Settings
3. Add push mirror with GitHub URL and PAT
4. Enable "Sync when commits are pushed"

## Resources

- [Gitea Documentation](https://docs.gitea.io/)
- [Gitea Mirror Setup](https://docs.gitea.com/usage/repo-mirror)
