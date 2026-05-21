# Francis — daily security digest

n8n workflow + supporting Python exporter + systemd units that produce
the morning Wazuh digest delivered to the dedicated "Francis" Telegram chat.

## Pipeline

```
06:45 ET   systemd timer fires francis-export-wazuh.service
           -> /usr/local/bin/francis-export-wazuh.py reads yesterday's
              alerts.json from the wazuh-manager docker volume,
              summarizes by level/rule/agent, captures critical (L>=12)
              full records, plus an SCA delta block (failed checks
              + same-day transitions). Writes JSON to:
              /home/serveradmin/docker_volumes/n8n/files/francis/
              wazuh-daily.json

07:00 ET   n8n cron fires workflow egiYz0MPZmHXlWrAfxrOC
           ("Francis — daily digest")
           -> reads the JSON, builds prompt, hits Anthropic Claude
              (claude-sonnet-4-6, system prompt: Francis persona),
              sends digest to Telegram chat -5168942238 via
              @Codistech_francis_bot.
```

## Files in this directory

| File | Live path on VM 100 |
|------|---------------------|
| `workflow.json` | n8n workflow id `egiYz0MPZmHXlWrAfxrOC`; mirrored at `/home/serveradmin/docker_volumes/n8n/files/francis/workflow.json` |
| `francis-export-wazuh.py` | `/usr/local/bin/francis-export-wazuh.py` (root:root 0755) |
| `francis-export-wazuh.service` | `/etc/systemd/system/francis-export-wazuh.service` |
| `francis-export-wazuh.timer` | `/etc/systemd/system/francis-export-wazuh.timer` |

## Updating the workflow

n8n imports do not always preserve the schedule trigger expression cleanly
when the JSON has both `expression` and `triggerAtMinute/Hour` fields.
When patching this workflow, ensure the `Cron 07:00 ET` node has ONLY:

```json
{ "field": "cronExpression", "expression": "0 7 * * *" }
```

The n8n container has `GENERIC_TIMEZONE=America/Detroit` so the cron
evaluates in ET (DST-aware).

Deploy a workflow change:

```bash
sudo docker cp workflow.json n8n:/tmp/francis.json
sudo docker exec n8n n8n import:workflow --input=/tmp/francis.json
sudo docker exec n8n n8n publish:workflow --id=egiYz0MPZmHXlWrAfxrOC
sudo docker restart n8n
```

After restart, n8n's startup log shows `Activated workflow "Francis — daily digest"`.

## Telegram bot + chat

| Item | Value |
|------|-------|
| Bot | `@Codistech_francis_bot` (id `8632150536`) |
| Chat | `-5168942238` ("Francis" group) |
| n8n credential | `JuP1hxzHyO1GKJMh` ("Francis Bot") |

## SCA delta section (added 2026-05-08)

The Python exporter now tracks SCA events from `rule.groups: ["sca"]`
alerts and produces a `sca_delta` block in the daily JSON:

- `total_sca_events` / `unique_checks_touched` / `by_policy`
- `new_failures` — checks ending the day in `failed` state (capped 50)
- `transitions` — checks that flipped passed↔failed within the day window

The n8n Build prompt node renders this into a "SCA delta" section in the
user prompt with explicit instruction to distinguish real config drift
from the recurring `sshd -T` scan-resolution artifact (UsePAM, MACs,
PermitUserEnvironment on Ubuntu agents).

Pairs with the bridge filter (commit `e7c75a3` in homelab-configs:
`wazuh/integrations/custom-alertmanager.py`) that prevents low-level
SCA from paging Telegram in real time.
