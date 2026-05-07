# Home Assistant

Home automation platform with local voice assistant capabilities.

## Overview

Home Assistant provides centralized control of smart home devices with a focus on privacy through local processing. This deployment includes a complete local voice assistant stack:

- **Home Assistant** — Core automation platform
- **Whisper** — Local speech-to-text (OpenAI Whisper)
- **Piper** — Local text-to-speech
- **OpenWakeWord** — Local wake word detection ("Ok Nabu")

## Why Home Assistant?

Selected over alternatives (SmartThings, Hubitat, openHAB) for:

- Privacy — All processing stays local
- Integration — 2000+ supported devices and services
- Automation — Powerful scripting and automation engine
- Community — Active development and add-on ecosystem
- No cloud dependency

## Architecture
```
┌─────────────────────────────────────────────────┐
│                Home Assistant                    │
│                   (core)                         │
└──────────┬──────────┬──────────┬────────────────┘
           │          │          │
     ┌─────▼────┐ ┌───▼───┐ ┌────▼────────┐
     │ Whisper  │ │ Piper │ │ OpenWakeWord│
     │  (STT)   │ │ (TTS) │ │   (wake)    │
     └──────────┘ └───────┘ └─────────────┘
           │          │          │
           └──────────┴──────────┘
                      │
              ┌───────▼───────┐
              │  Voice Sats   │
              │ (ESP32/etc)   │
              └───────────────┘
```

## NIST 800-53 Control Mapping

| Control Family | Controls Addressed | Implementation |
|----------------|-------------------|----------------|
| SC (System & Communications) | SC-8 | Local processing, no cloud transmission |
| AC (Access Control) | AC-3, AC-6 | User authentication, device permissions |
| SI (System Integrity) | SI-4 | Device monitoring and alerting |

## Voice Assistant Components

| Service | Purpose | Model |
|---------|---------|-------|
| Whisper | Speech-to-text | small-int8 (fast, accurate) |
| Piper | Text-to-speech | en_US-lessac-medium |
| OpenWakeWord | Wake word detection | ok_nabu |

## Deployment
```bash
# Start all services
docker-compose up -d

# Access at https://ha.yourdomain.com
# Complete onboarding wizard on first run
```

## Configuration

Configuration is stored in `./config` and persists across restarts. Key files:

- `configuration.yaml` — Main config
- `automations.yaml` — Automation rules
- `scripts.yaml` — Reusable scripts
- `secrets.yaml` — Sensitive values (gitignored)

## Voice Satellite Setup

ESP32-based satellites connect to the Wyoming services for distributed voice control:

1. Flash ESPHome to ESP32-S3 with INMP441 mic + MAX98357A speaker
2. Configure Wyoming satellite integration
3. Assign to rooms in Home Assistant

## Resources

- [Home Assistant Docs](https://www.home-assistant.io/docs/)
- [Wyoming Protocol](https://github.com/rhasspy/wyoming)
- [Year of the Voice](https://www.home-assistant.io/voice_control/)
