# Wazuh -> Alertmanager bridge

Forwards Wazuh alerts of `rule.level >= 8` into Alertmanager's `/api/v2/alerts`
endpoint so Wazuh becomes a real-time signal source on the same Telegram
routes used by Prometheus alerts.

## Files

- `custom-alertmanager` - shell wrapper (Wazuh integrator entry point)
- `custom-alertmanager.py` - Python script that translates Wazuh alert JSON
  to Alertmanager v2 format and POSTs

## Severity mapping

| Wazuh `rule.level` | Alertmanager `severity` label | Existing AM route |
|---|---|---|
| >= 12 | `critical` | telegram-critical (group 10s, repeat 30m) |
| 8 - 11 | `warning` | telegram-warning (group 10m, repeat 4h) |
| < 8 | (filtered out at Wazuh integrator level) | n/a |

## Install

The Wazuh manager runs containerized. The integrations directory is a named
docker volume (`single-node_wazuh_integrations`), so files must be copied
inside the container or onto the volume's host path.

```bash
# 1) Copy files into the integrations volume
INT_VOL=/var/lib/docker/volumes/single-node_wazuh_integrations/_data
sudo cp custom-alertmanager custom-alertmanager.py $INT_VOL/

# 2) Match Wazuh's expected ownership and permissions INSIDE the container
#    (gid mapping differs between host and container - chown there).
sudo docker exec single-node-wazuh.manager-1 sh -c '
  chown root:wazuh /var/ossec/integrations/custom-alertmanager /var/ossec/integrations/custom-alertmanager.py
  chmod 750 /var/ossec/integrations/custom-alertmanager /var/ossec/integrations/custom-alertmanager.py
'

# 3) Add the <integration> block to the manager config
#    (host path: /home/serveradmin/docker_volumes/wazuh/wazuh-docker/single-node/config/wazuh_cluster/wazuh_manager.conf)
#    Insert before the FIRST </ossec_config> closing tag:
```

```xml
<!-- Alertmanager bridge: rule level >= 8 -> AM -> existing telegram routes -->
<integration>
  <name>custom-alertmanager</name>
  <hook_url>http://alertmanager:9093/api/v2/alerts</hook_url>
  <level>8</level>
  <alert_format>json</alert_format>
</integration>
```

The hook URL uses the docker DNS name `alertmanager`, resolvable because the
Wazuh manager and Alertmanager containers share an external docker bridge
network named `monitoring-bridge`. This keeps the bridge traffic on a private
docker network instead of routing through a LAN-exposed published port (which
would let any host on the LAN POST fake alerts to Alertmanager).

If `monitoring-bridge` does not yet exist, create it before bringing the
stacks up:

```bash
docker network create monitoring-bridge
```

Both `opensense-monitoring/docker-compose.yaml` and `wazuh/docker-compose.yml`
declare it as `external: true` and attach the relevant services.

```bash
# 4) Restart the manager
sudo docker restart single-node-wazuh.manager-1

# 5) Verify integrator picked it up
sudo docker exec single-node-wazuh.manager-1 sh -c '
  tail -50 /var/ossec/logs/ossec.log | grep -i integrator
'
# Expect: "wazuh-integratord: INFO: Enabling integration for: 'custom-alertmanager'."
```

## Verify end-to-end

Trigger a level >= 8 event (e.g. SSH brute-force) and check Alertmanager:

```bash
curl -s http://10.0.X.Y:9093/api/v2/alerts \
  | jq '.[] | select(.labels.alertname=="WazuhAlert") | {severity:.labels.severity, rule:.labels.wazuh_rule_id, level:.labels.wazuh_rule_level, state:.status.state}'
```

## Troubleshooting

- **No alerts reach AM, integrations.log is 0 bytes**: ownership/perms issue.
  The host's `wazuh` group GID differs from the container's. Fix by chown'ing
  *inside the container* (step 2 above), not on the host.
- **`integrator.log` shows JSON errors**: usually the alert payload contains
  characters that break the AM label-value regex. Truncate or sanitize in
  `custom-alertmanager.py` before building the payload.
- **AM returns 4xx**: check the hook URL is reachable from inside the manager
  container - `docker exec ... curl http://10.200.2.1:9093/api/v2/status`.
