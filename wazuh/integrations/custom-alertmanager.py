#!/usr/bin/env python3
"""
Wazuh -> Alertmanager bridge.

Wazuh integrator calling convention:
    argv[1] = path to a JSON file containing the alert
    argv[2] = api key (unused — Alertmanager doesn't require auth in our setup)
    argv[3] = hook URL (Alertmanager v2 alerts endpoint)

Severity mapping (Wazuh rule.level -> AM severity label):
    >= 12  -> critical
    >= 8   -> warning
    else   -> info  (won't normally reach this script if <integration> level >= 8)
"""
import json
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone


def main():
    if len(sys.argv) < 4:
        sys.exit(0)

    alert_path = sys.argv[1]
    hook_url = sys.argv[3]

    with open(alert_path, 'r') as f:
        alert = json.load(f)

    rule = alert.get('rule', {}) or {}
    agent = alert.get('agent', {}) or {}

    level = int(rule.get('level', 0) or 0)
    if level >= 12:
        severity = 'critical'
    elif level >= 8:
        severity = 'warning'
    else:
        severity = 'info'

    rule_id = str(rule.get('id', ''))
    rule_desc = rule.get('description', 'Wazuh alert')
    groups = rule.get('groups', []) or []
    agent_name = agent.get('name', 'unknown')
    agent_id = str(agent.get('id', ''))

    # Alertmanager label values must be valid UTF-8 strings.
    # Cap groups label so we don't blow past AM's de-facto limits.
    groups_label = ','.join(groups)[:200]

    # Use the rule description in the summary; truncate full_log for the
    # description annotation so we don't ship huge payloads.
    full_log = (alert.get('full_log') or '')[:1000]
    location = alert.get('location', '') or ''

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')

    payload = [{
        'labels': {
            'alertname': 'WazuhAlert',
            'severity': severity,
            'wazuh_rule_id': rule_id,
            'wazuh_rule_level': str(level),
            'agent': agent_name,
            'agent_id': agent_id,
            'instance': agent_name,
            'groups': groups_label,
            'source': 'wazuh',
        },
        'annotations': {
            'summary': f'[L{level}] {rule_desc}',
            'description': full_log or rule_desc,
            'location': location,
        },
        'startsAt': now,
        # Replace with your actual Wazuh dashboard URL.
        'generatorURL': 'http://wazuh-dashboard.local.example.home/',
    }]

    req = urllib.request.Request(
        hook_url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST',
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            sys.exit(0 if resp.status < 300 else 1)
    except urllib.error.URLError:
        sys.exit(1)
    except Exception:
        sys.exit(1)


if __name__ == '__main__':
    main()
