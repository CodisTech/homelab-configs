# CRL inbound funnel — n8n workflows

Source-of-truth for the n8n workflows that handle the CyberReadyLabs inbound lead funnel:

- `/webhook/contact-intake` — front-door Tally form (cyberreadylabs.com)
- `/webhook/calcom-x7kP9mR3vL2nQ8wF` — Cal.com 15-minute discovery booking

The 2026-05-08 change adds a `lead_type` qualifier so vendor / recruiter / other inquiries are still captured (Notion record with `Status='Disqualified'`, `Lead Type=<reason>`) but skip the prospect-onboarding email and use a lighter Telegram message.

See `funnel-screening.md` for the full runbook (why, what, manual UI work in Tally / Cal.com / Notion).

## Files in this directory

| File | Purpose |
|------|---------|
| `funnel-screening.md` | Runbook — what changed, why, and required manual UI work |
| `transform.py` | Idempotent transformer: takes original n8n exports → produces `*.prod.json` + `*.staging.json` |
| `smoke-test.sh` | End-to-end test against staging or production webhook paths (5 cases per webhook) |
| `contact-form.prod.json` | n8n workflow JSON for production import (id `RidzLH7xQ8WHLk9Q`, path `contact-intake`) |
| `contact-form.staging.json` | Staging variant (no id, path `contact-intake-staging`) |
| `calcom-booking.prod.json` | Production Cal.com workflow (id `VMv0EOCNmDIbUvcf`, path `calcom-x7kP9mR3vL2nQ8wF`) — signing secret REDACTED |
| `calcom-booking.staging.json` | Staging Cal.com workflow — signing secret REDACTED |
| `deploy.sh` | Helper: rehydrates secret + imports staging (`./deploy.sh stage`) or production (`./deploy.sh promote`) |

## Secret handling

The Cal.com webhook signing secret is **redacted to `__CALCOM_WEBHOOK_SECRET__`** in committed `*.json` files. Reason: this Gitea repo mirrors to public `github.com/CodisTech/homelab-configs` every 5 minutes via `mirror-to-github.sh`; `scrub.sh` does not yet recognize the Cal.com secret pattern.

The deploy script (`deploy.sh`) reads the live secret from the running n8n workflow's `Verify Signature` node before importing, then writes it back. The redaction is purely a Gitea-track-it-without-leaking measure; live n8n always has the real secret.

If both staging and production Cal.com workflows are missing simultaneously (cold-start scenario), recover the secret from:
1. n8n's `workflow_history` table on VM 100 — old versions retain the original jsCode
2. Cal.com webhook configuration UI (settings → webhook → reveal signing secret)
3. Or rotate it: generate a new secret, update both Cal.com webhook config and the n8n workflow

## Editing workflow

```bash
# 1. Pull a fresh export of a live workflow from n8n
ssh serveradmin@10.0.60.11
sudo docker exec n8n n8n export:workflow --id=<id> --output=/tmp/wf.json
sudo docker cp n8n:/tmp/wf.json /tmp/

# 2. Edit transform.py if the change is structural
# 3. Re-run transform.py to regenerate prod + staging JSONs
python3 transform.py --in-dir /tmp/crl-workflows --out-dir /tmp/crl-out

# 4. Re-redact the calcom secret before commit
#    (transform.py preserves whatever was in the input; re-redact if you started from a fresh export)

# 5. Stage, smoke-test, then promote
./deploy.sh stage
./smoke-test.sh staging
./deploy.sh promote
```

## Rollback

n8n's `workflow_history` table preserves prior versions. To roll back via UI:

1. Open the workflow in n8n editor
2. Workflow menu → Versions
3. Pick a pre-change version (look for an entry from before 2026-05-08)
4. Restore

Or re-export the prior version's JSON, redact secrets, and `n8n import:workflow --input=<file>`.

## Related

- `feedback_cyberreadylabs_deploy_workflow.md` (memory) — overall CRL deploy pattern
- `feedback_gitea_only_github_mirror.md` (memory) — why we never push directly to GitHub
- `n8n/workflows/francis/` — same source-of-truth pattern, different workflow family
