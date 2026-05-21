# Wazuh SIEM — Enterprise Security Monitoring

> Production SIEM deployment monitoring a segmented homelab infrastructure with 2,337+ vulnerability triages, custom detection rules, and NIST 800-53 control mapping.

## The Problem

Most homelabs run services with no centralized visibility into what's actually happening across the network. Containers get deployed, configurations drift, and there's no audit trail. In an enterprise, this is exactly the gap that leads to breaches going undetected for months.

I needed the same level of security monitoring for my infrastructure that I implemented aboard USS Nimitz — centralized log collection, real-time alerting, file integrity monitoring, and compliance-ready reporting.

## What This Deployment Does

This is not a tutorial follow-along. This is a production SIEM monitoring real services across a segmented network:

- **2,337 vulnerabilities triaged** — including 8 critical findings requiring immediate remediation
- **Multi-agent deployment** across Linux hosts, Docker containers, and Windows endpoints
- **Custom detection rules** tailored to my specific infrastructure and threat model
- **File integrity monitoring (FIM)** across critical configuration files and Docker volumes
- **Active response** configured for automated threat mitigation
- **NIST 800-53 control mapping** — every capability maps to specific compliance requirements

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Network Segments                       │
│                                                          │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐   │
│  │ VLAN 10 │  │ VLAN 20 │  │ VLAN 30 │  │ VLAN 40 │   │
│  │ Mgmt    │  │ Services│  │ IoT     │  │ Business│   │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘   │
│       │            │            │            │          │
│       └────────────┴────────────┴────────────┘          │
│                         │                                │
│                    Wazuh Agents                          │
│                         │                                │
│              ┌──────────▼──────────┐                     │
│              │    Wazuh Manager    │                     │
│              │   Rule Processing   │                     │
│              │   Active Response   │                     │
│              └──────────┬──────────┘                     │
│                         │                                │
│              ┌──────────▼──────────┐                     │
│              │   Wazuh Indexer     │                     │
│              │   (OpenSearch)      │                     │
│              └──────────┬──────────┘                     │
│                         │                                │
│              ┌──────────▼──────────┐                     │
│              │  Wazuh Dashboard    │                     │
│              │  Compliance Reports │                     │
│              └─────────────────────┘                     │
└──────────────────────────────────────────────────────────┘
```

## Results

| Metric | Value |
|--------|-------|
| Total vulnerabilities triaged | 2,337 |
| Critical findings remediated | 8 |
| Agents deployed | Multiple across VLANs |
| Custom rules created | Active detection rules tailored to infrastructure |
| Compliance frameworks mapped | NIST 800-53 (AU, SI, IR, CA, RA, SC families) |
| Mean time to detection | Near real-time alerting on critical events |

## NIST 800-53 Control Mapping

| Control Family | Controls Addressed | Implementation |
|---------------|-------------------|----------------|
| AU (Audit and Accountability) | AU-2, AU-3, AU-6, AU-12 | Centralized log collection, automated review, event correlation |
| SI (System and Information Integrity) | SI-4, SI-7 | File integrity monitoring, real-time malware detection, vulnerability scanning |
| IR (Incident Response) | IR-4, IR-5, IR-6 | Automated alerting, active response playbooks, incident tracking |
| CA (Assessment and Authorization) | CA-7 | Continuous monitoring dashboard, compliance reporting |
| RA (Risk Assessment) | RA-5 | Vulnerability detection and prioritized remediation |
| SC (System and Communications Protection) | SC-7 | Network segmentation monitoring, boundary protection alerts |

## Why Wazuh Over Splunk/ELK/Graylog

| Criteria | Wazuh | Splunk | ELK Stack |
|----------|-------|--------|-----------|
| License cost | Free/open source | $$$$ | Free (OSS) / Paid |
| Native compliance reporting | PCI-DSS, HIPAA, NIST | Plugin-dependent | Manual config |
| Built-in FIM | Native | Add-on | Auditbeat |
| Active response | Native | SOAR add-on | Custom scripting |
| Resource footprint | Moderate | Heavy | Heavy |

## Key Technical Decisions

**Docker deployment over bare metal** — Enables version-controlled infrastructure, easier upgrades, and consistent environments. The docker-compose.yml in this repo is the actual production configuration.

**Dedicated indexer tuning** — Default JVM heap was insufficient. Increased to 2GB minimum after experiencing indexer crashes under log volume from multiple agents.

**SSL certificate management** — Generated certificates before first startup using Wazuh cert generator. Self-signed certs for internal traffic, managed through the config directory.

**Custom decoder/rule workflow** — All custom rules tested in staging before promotion to production. Rules tuned iteratively based on false positive analysis.

## Deployment

```bash
git clone https://github.com/CodisTech/homelab-configs.git
cd homelab-configs/wazuh

# Copy environment template
cp .env.example .env

# Edit with your passwords
nano .env

# Generate SSL certificates (required before first run)
docker run -v ./config/wazuh_indexer_ssl_certs:/certs wazuh/wazuh-certs-generator

# Start services
docker-compose up -d
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

1. **Memory matters** — The Wazuh Indexer (OpenSearch) needs minimum 2GB JVM heap. Default settings will cause crashes under real log volume.

2. **Certificate generation is not optional** — SSL certs must be generated before first startup. Attempting to start without them leads to silent failures.

3. **Tune before you trust** — Default rules generate significant noise. The path from 2,337 raw findings to actionable intelligence required iterative tuning of severity levels, whitelisting known-good behaviors, and creating custom rules.

4. **FIM scope requires thought** — Monitoring too many directories creates alert fatigue. Start with critical paths (Docker configs, SSH keys, system binaries) and expand based on actual threat modeling.

5. **Network segmentation visibility** — Deploying agents across VLANs revealed cross-segment traffic patterns that were not visible at the firewall level. This informed firewall rule refinements.

## What's Next

- Integration with CrowdSec for correlated threat intelligence
- Automated vulnerability report generation for CyberReadyLabs client assessments
- Custom dashboards for executive-level reporting
- MITRE ATT&CK framework mapping for detection coverage analysis

## Resources

- [Wazuh Documentation](https://documentation.wazuh.com/)
- [NIST 800-53 Rev 5](https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final)
- [Wazuh Docker Deployment Guide](https://documentation.wazuh.com/current/deployment-options/docker/index.html)
