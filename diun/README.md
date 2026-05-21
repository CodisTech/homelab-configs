# Diun

Docker Image Update Notifier — sends Telegram alerts when container images have updates available.

## Overview

Diun monitors all running Docker containers and notifies you via Telegram when newer versions are available. Part of the GitOps workflow for this homelab.

## Why Diun?

Selected over alternatives (Watchtower, Ouroboros) for:

- **Notification only** — Doesn't auto-update, you stay in control
- **Lightweight** — Single binary, minimal resources
- **Multiple notifiers** — Telegram, Discord, Slack, email, etc.
- **Registry support** — Docker Hub, GHCR, custom registries

## GitOps Workflow
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Diun     │────▶│  Telegram   │────▶│     You     │
│  (scanner)  │     │   (alert)   │     │  (review)   │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                               │
                                        ┌──────▼──────┐
                                        │   Gitea     │
                                        │ (update PR) │
                                        └──────┬──────┘
                                               │
                                        ┌──────▼──────┐
                                        │ Production  │
                                        │  (deploy)   │
                                        └─────────────┘
```

1. Diun scans running containers daily at 8 AM
2. Sends Telegram notification if updates exist
3. You update compose file in Gitea
4. Pull changes to production and redeploy

## NIST 800-53 Control Mapping

| Control Family | Controls Addressed | Implementation |
|----------------|-------------------|----------------|
| SI (System Integrity) | SI-2 | Flaw remediation awareness |
| CM (Configuration Management) | CM-3 | Change control notification |
| SA (System & Services Acquisition) | SA-10 | Software update monitoring |

## Deployment
```bash
cp .env.example .env
nano .env  # Add Telegram bot token and chat ID

docker-compose up -d
```

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `TELEGRAM_TOKEN` | Telegram bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID |

### Schedule

Default: Daily at 8 AM (`0 8 * * *`)

Change via `DIUN_WATCH_SCHEDULE` environment variable.

### Creating a Telegram Bot

1. Message @BotFather on Telegram
2. Send `/newbot`
3. Follow prompts to get token
4. Message your bot, then get chat ID from:
```
   https://api.telegram.org/bot<TOKEN>/getUpdates
```

## Resources

- [Diun Documentation](https://crazymax.dev/diun/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
