# Wazuh SIEM

Security Information and Event Management (SIEM) deployment using Wazuh for centralized log collection, threat detection, and compliance monitoring.

## Overview

This deployment provides:
- **Wazuh Manager** — Agent management, rule processing, and alerting
- **Wazuh Indexer** — Log storage and search (OpenSearch-based)
- **Wazuh Dashboard** — Visualization and analysis interface

## Why Wazuh?

Selected over alternatives (Splunk, ELK, Graylog) for:
- Open source with no license costs
- Native compliance reporting (PCI-DSS, HIPAA, NIST 800-53)
- Built-in file integrity monitoring (FIM)
- Active response capabilities
- Strong agent support across Linux, Windows, and macOS

## Architecture
```
┌─────────────────┐     ┌─────────────────┐
│  Wazuh Agents   │────▶│  Wazuh Manager  │
│ (endpoints)     │     │  (1514/1515)    │
└─────────────────┘     └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  Wazuh Indexer  │
                        │  (9200)         │
                        └────────┬────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │ Wazuh Dashboard │
                        │  (5601)         │
                        └─────────────────┘
```

## NIST 800-53 Control Mapping

| Control Family | Controls Addressed | Implementation |
|----------------|-------------------|----------------|
| AU (Audit) | AU-2, AU-3, AU-6, AU-12 | Centralized log collection and review |
| SI (System Integrity) | SI-4, SI-7 | File integrity monitoring, malware detection |
| IR (Incident Response) | IR-4, IR-5, IR-6 | Alerting, active response, incident tracking |
| CA (Assessment) | CA-7 | Continuous monitoring dashboard |

## Deployment
```bash
# Copy environment template
cp .env.example .env

# Edit with your passwords
nano .env

# Start services
docker-compose up -d
```

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `INDEXER_PASSWORD` | Password for indexer admin user |
| `API_PASSWORD` | Password for Wazuh API |
| `DASHBOARD_PASSWORD` | Password for dashboard access |

### SSL Certificates

Generate certificates before first run:
```bash
docker run -v ./config/wazuh_indexer_ssl_certs:/certs wazuh/wazuh-certs-generator
```

## Agent Deployment
```bash
# Linux
curl -s https://packages.wazuh.com/4.x/apt/pool/main/w/wazuh-agent/wazuh-agent_4.14.2-1_amd64.deb -o wazuh-agent.deb
WAZUH_MANAGER="your-manager-ip" dpkg -i wazuh-agent.deb

# Windows (PowerShell)
Invoke-WebRequest -Uri https://packages.wazuh.com/4.x/windows/wazuh-agent-4.14.2-1.msi -OutFile wazuh-agent.msi
msiexec.exe /i wazuh-agent.msi /q WAZUH_MANAGER="your-manager-ip"
```

## Lessons Learned

- Allocate sufficient memory for the indexer (minimum 2GB JVM heap)
- SSL certificate generation is required before first startup
- Custom decoders/rules should be tested in a non-production environment first

## Resources

- [Wazuh Documentation](https://documentation.wazuh.com/)
- [NIST 800-53 Rev 5](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
