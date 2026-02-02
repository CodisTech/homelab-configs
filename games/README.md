# Games

Game servers for family entertainment.

## Minecraft

Paper server with Java and Bedrock crossplay support.

### Features

- **Paper** — Optimized Minecraft server with plugin support
- **Version** — 1.21.4
- **Memory** — 8GB allocated
- **Crossplay** — Java (25565) and Bedrock (19132) clients supported

### Deployment
```bash
cd minecraft
docker-compose up -d
```

### Ports

| Port | Protocol | Purpose |
|------|----------|---------|
| 25565 | TCP | Java Edition |
| 19132 | UDP | Bedrock Edition (crossplay) |

### Configuration

Server settings are stored in `./data/server.properties` after first run. Edit to customize gameplay.

### Resources

- [itzg/minecraft-server](https://github.com/itzg/docker-minecraft-server)
- [Paper MC](https://papermc.io/)
