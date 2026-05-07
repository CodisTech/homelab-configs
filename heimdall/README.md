# Heimdall

Application dashboard for quick access to all homelab services.

## Overview

Heimdall provides a clean, customizable start page with links to all self-hosted services. Supports enhanced applications with API integrations for live status.

## Why Heimdall?

Selected over alternatives (Homer, Organizr, Homarr) for:

- Simple, clean interface
- Enhanced app support with live stats
- LinuxServer.io maintained image
- Low resource usage
- Easy configuration via web UI

## Features

- Customizable layout and themes
- Application categories
- Enhanced apps with API integration
- Search functionality
- Mobile-friendly responsive design

## Deployment
```bash
# Start service
docker-compose up -d

# Access at https://heimdall.yourdomain.com
# Configure apps through the web interface
```

## Configuration

Configuration is stored in the mounted `/config` volume and persists across container restarts.

### Adding Applications

1. Click the app icon in the dashboard
2. Select "Add" 
3. Choose from pre-configured apps or add custom
4. Enter URL and optional API credentials for enhanced features

## Security

Container runs with `no-new-privileges` security option to prevent privilege escalation.

## Resources

- [Heimdall GitHub](https://github.com/linuxserver/Heimdall)
- [LinuxServer.io](https://docs.linuxserver.io/images/docker-heimdall)
