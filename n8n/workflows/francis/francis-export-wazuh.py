#!/usr/bin/env python3
"""
Francis: Wazuh daily export.

Reads yesterday's alerts from the Wazuh manager log, summarizes by level
and rule, includes full details for level >= 12, plus an SCA delta section
(checks ending failed + same-day passed/failed transitions). Writes a single
JSON summary file that n8n's Francis workflow consumes.

The output path is inside the n8n bind-mount so the n8n container can
read it at /home/node/.n8n-files/francis/wazuh-daily.json.
"""

import gzip
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

ALERTS_DIR = Path("/var/lib/docker/volumes/single-node_wazuh_logs/_data/alerts")
LIVE_ALERTS = ALERTS_DIR / "alerts.json"
OUT_FILE = Path("/home/serveradmin/docker_volumes/n8n/files/francis/wazuh-daily.json")
CRIT_LEVEL = 12
TOP_RULES_N = 20
SAMPLE_LOG_CHARS = 500
SCA_MAX_FAILURES = 50


def parse_ts(s):
    s = s.replace("Z", "+00:00")
    if s.endswith("+0000"):
        s = s[:-5] + "+00:00"
    return datetime.fromisoformat(s)


def open_for_day(day):
    archive = ALERTS_DIR / f"{day.year}" / day.strftime("%b") / f"ossec-alerts-{day.day:02d}.json.gz"
    if archive.exists():
        return archive, gzip.open(archive, "rt", encoding="utf-8", errors="replace")
    if LIVE_ALERTS.exists():
        return LIVE_ALERTS, LIVE_ALERTS.open("r", encoding="utf-8", errors="replace")
    return None, None


def main():
    now = datetime.now(timezone.utc)
    until = now.replace(hour=0, minute=0, second=0, microsecond=0)
    since = until - timedelta(days=1)

    by_level = Counter()
    by_rule = Counter()
    by_agent = Counter()
    # Track the level for each (rule_id, description) seen. Same rule_id can
    # technically fire at different levels via local overrides; record the max
    # so verifier thresholds catch the worst case. Added 2026-05-20 to close
    # the verifier hallucination class: previously top_rules had no level so
    # the verifier inferred level from description text and got it wrong
    # (e.g. rule 86601 inferred as L≥10 from "EXPLOIT" wording, actual L3).
    rule_levels = {}
    critical = []
    total = 0

    sca_events = defaultdict(list)
    sca_total = 0
    sca_by_policy = Counter()

    src_path, src = open_for_day(since)
    if src is None:
        print(f"no alerts source found under {ALERTS_DIR}", file=sys.stderr)
        sys.exit(1)

    with src as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                a = json.loads(line)
                ts = parse_ts(a["timestamp"])
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
            if not (since <= ts < until):
                continue

            total += 1
            level = int(a.get("rule", {}).get("level", 0))
            rule_id = a.get("rule", {}).get("id", "?")
            rule_desc = a.get("rule", {}).get("description", "")
            rule_groups = a.get("rule", {}).get("groups", []) or []
            agent = a.get("agent", {}).get("name", "?")

            by_level[level] += 1
            by_rule[(rule_id, rule_desc)] += 1
            by_agent[agent] += 1
            # Record the highest level observed for this rule_id
            if level > rule_levels.get(rule_id, -1):
                rule_levels[rule_id] = level

            if level >= CRIT_LEVEL:
                critical.append({
                    "timestamp": a["timestamp"],
                    "level": level,
                    "rule_id": rule_id,
                    "description": rule_desc,
                    "agent": agent,
                    "full_log": (a.get("full_log") or "")[:SAMPLE_LOG_CHARS],
                })

            if "sca" in rule_groups:
                sca = a.get("data", {}).get("sca", {}) or {}
                check = sca.get("check") or {}
                check_id = check.get("id")
                if check_id is not None:
                    result = check.get("result", "?")
                    title = (check.get("title") or "")[:200]
                    policy = sca.get("policy", "?")
                    sca_events[(agent, str(check_id))].append((ts, result, title, policy))
                    sca_total += 1
                    sca_by_policy[policy] += 1

    new_failures = []
    transitions = []

    for (agent, check_id), events in sca_events.items():
        events.sort(key=lambda e: e[0])
        last_ts, last_result, title, policy = events[-1]
        results_seen = {e[1] for e in events}

        if last_result == "failed":
            new_failures.append({
                "agent": agent,
                "check_id": check_id,
                "title": title,
                "policy": policy,
                "last_seen": last_ts.isoformat(),
            })

        if len(results_seen) > 1:
            transitions.append({
                "agent": agent,
                "check_id": check_id,
                "title": title,
                "policy": policy,
                "from": events[0][1],
                "to": last_result,
                "events_today": len(events),
            })

    new_failures.sort(key=lambda x: (x["policy"], x["agent"], x["check_id"]))
    transitions.sort(key=lambda x: (x["policy"], x["agent"], x["check_id"]))
    new_failures = new_failures[:SCA_MAX_FAILURES]

    summary = {
        "generated_at": now.isoformat(),
        "window_since": since.isoformat(),
        "window_until": until.isoformat(),
        "source_file": str(src_path),
        "total_alerts": total,
        "by_level": {str(k): v for k, v in sorted(by_level.items())},
        "top_rules": [
            {"rule_id": r[0], "description": r[1], "count": c,
             "level": rule_levels.get(r[0], 0)}
            for r, c in by_rule.most_common(TOP_RULES_N)
        ],
        "by_agent": dict(by_agent.most_common()),
        "critical_alerts": critical,
        "sca_delta": {
            "total_sca_events": sca_total,
            "unique_checks_touched": len(sca_events),
            "by_policy": dict(sca_by_policy.most_common()),
            "new_failures": new_failures,
            "transitions": transitions,
        },
    }

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT_FILE.with_suffix(".tmp")
    with tmp.open("w") as f:
        json.dump(summary, f, indent=2, default=str)
    os.replace(tmp, OUT_FILE)
    os.chmod(OUT_FILE, 0o644)

    print(
        f"francis-export-wazuh: wrote {total} alerts "
        f"({len(critical)} critical, {sca_total} sca events, "
        f"{len(new_failures)} failed checks, {len(transitions)} transitions) "
        f"to {OUT_FILE}"
    )


if __name__ == "__main__":
    main()
