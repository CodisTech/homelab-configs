# Nginx

Web server for static content hosting.

## Overview

Nginx serves static websites and content. Currently used for the CodisTech landing page.

## Deployment
```bash
docker-compose up -d
```

## Configuration

### Volumes

| Path | Purpose |
|------|---------|
| `./templates` | Nginx config templates |
| `./html` | Static website files |

## Security

Container runs with `no-new-privileges` security option to prevent privilege escalation.

## Resources

- [Nginx Documentation](https://nginx.org/en/docs/)
