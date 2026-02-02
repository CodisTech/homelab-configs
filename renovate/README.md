# Renovate

Automated dependency update PRs for Docker images.

## Overview

Renovate scans your repos for outdated Docker images and creates Pull Requests to update them. Part of the GitOps workflow.

## Why Renovate?

- **PRs for review** — You approve updates before they happen
- **Supports Gitea** — Self-hosted, no cloud dependency
- **Docker-aware** — Understands docker-compose files
- **Configurable** — Fine-grained control over updates

## GitOps Workflow
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Renovate   │────▶│   Gitea     │────▶│     You     │
│  (scanner)  │     │    (PR)     │     │  (review)   │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                        ┌──────▼──────┐
                                        │   Merge     │
                                        └──────┬──────┘
                                               │
                                        ┌──────▼──────┐
                                        │ Production  │
                                        │ git pull    │
                                        │ docker up   │
                                        └─────────────┘
```

## NIST 800-53 Control Mapping

| Control Family | Controls Addressed | Implementation |
|----------------|-------------------|----------------|
| SI (System Integrity) | SI-2 | Automated flaw remediation |
| CM (Configuration Management) | CM-3, CM-4 | Change control via PRs |
| SA (System & Services Acquisition) | SA-10 | Software update management |

## Deployment
```bash
cp .env.example .env
nano .env  # Add Gitea token

# Run manually
docker-compose run --rm renovate

# Or let cron run it daily at 9 AM
```

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `GITEA_TOKEN` | Gitea access token with repo and issue permissions |

### Gitea Token Permissions

Create token at `https://your-gitea/user/settings/applications` with:
- `read:user`
- `write:repository`
- `read:repository`
- `write:issue`
- `read:issue`

### Schedule

Runs daily at 9 AM via cron (after Diun's 8 AM notification scan).

## Resources

- [Renovate Documentation](https://docs.renovatebot.com/)
- [Renovate Gitea Setup](https://docs.renovatebot.com/modules/platform/gitea/)
