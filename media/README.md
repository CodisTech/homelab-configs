# Media

Media server stack for streaming movies, TV shows, and music.

## Services

| Service | Purpose | Port |
|---------|---------|------|
| Plex | Primary media server | 32400 |
| Emby | Alternative media server | 8096 |

## Plex

Full-featured media server with apps for all platforms.

### Features

- Hardware transcoding (Intel QuickSync)
- Remote streaming
- Multi-user support
- Mobile sync
- Live TV & DVR (with tuner)

### Deployment
```bash
cd plex
cp .env.example .env

# Get claim token from https://plex.tv/claim
nano .env

docker-compose up -d
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `PUID` | User ID for file permissions |
| `PGID` | Group ID for file permissions |
| `PLEX_CLAIM` | Claim token from plex.tv/claim (expires in 4 min) |

## Emby

Alternative media server with similar features to Plex.

### Deployment
```bash
cd emby
docker-compose up -d
```

## Storage

Both services mount media from NFS share at `/mnt/nfs_share/` providing centralized storage from Unraid.

## Resources

- [Plex](https://www.plex.tv/)
- [Emby](https://emby.media/)
- [LinuxServer.io](https://docs.linuxserver.io/)
