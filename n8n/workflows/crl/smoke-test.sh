#!/usr/bin/env bash
# Smoke test for the lead-type filtering changes on the CRL inbound funnel.
#
# Usage (run on VM 100):
#   ./smoke-test.sh staging        # hit -staging webhook paths
#   ./smoke-test.sh production     # hit production paths (use after promotion)
#
# What it does:
# - Posts 5 test payloads against /webhook/contact-intake[-staging]
#     (no lead_type → defaults prospect; explicit prospect; vendor_partner; recruiter; other)
# - Posts 5 test payloads against /webhook/calcom-x7kP9mR3vL2nQ8wF[-staging]
#     with valid HMAC-SHA256 signatures computed against the live signing secret
#     read from the n8n DB.
# - Reports the HTTP status of each call. Manual verification of the Notion
#     record happens via the dashboard — this script only proves the webhook
#     accepted the payload and the workflow ran.
#
# Requirements: bash, curl, jq, openssl. No external secret files. The Cal.com
# signing secret is extracted from the workflow JSON itself.

set -euo pipefail

ENV="${1:-staging}"
case "$ENV" in
  staging)    SUFFIX="-staging" ;;
  production) SUFFIX="" ;;
  *) echo "usage: $0 staging|production" >&2 ; exit 2 ;;
esac

BASE="https://n8n-webhook.example.home/webhook"
CONTACT_PATH="contact-intake${SUFFIX}"
CALCOM_PATH="calcom-x7kP9mR3vL2nQ8wF${SUFFIX}"

EMAIL_PREFIX="smoketest-$(date +%s)"

cf_payload() {
  local lead_type="$1"
  local label="$2"
  cat <<EOF
{"data":{"first_name":"Smoke","last_name":"$label","email":"${EMAIL_PREFIX}-${label}@example.test","company_name":"SmokeTest LLC","role":"Tester","driver":"smoketest","budget":"none","how_many_employees":"1","url":"https://example.test"$( [ -n "$lead_type" ] && echo ",\"lead_type\":\"$lead_type\"" )}}
EOF
}

calcom_payload() {
  local lead_type="$1"
  local label="$2"
  local responses
  if [ -n "$lead_type" ]; then
    responses=", \"responses\": { \"lead_type\": { \"label\": \"Lead Type\", \"value\": \"$lead_type\" } }"
  else
    responses=""
  fi
  cat <<EOF
{"triggerEvent":"BOOKING_CREATED","payload":{"title":"15-Minute Discovery Call","startTime":"2026-06-01T15:00:00Z","attendees":[{"name":"Smoke $label","email":"${EMAIL_PREFIX}-cal-${label}@example.test"}]${responses}}}
EOF
}

post_contact() {
  local label="$1" lead_type="$2"
  local body status
  body=$(cf_payload "$lead_type" "$label")
  status=$(curl -sS -o /dev/null -w "%{http_code}" \
    -X POST "$BASE/$CONTACT_PATH" \
    -H "Content-Type: application/json" \
    -d "$body")
  printf "  contact-intake [%-15s] HTTP %s\n" "$label" "$status"
}

# Get the Cal.com signing secret from the live workflow JSON without printing it.
get_calcom_secret() {
  local id
  if [ "$ENV" = "staging" ]; then
    # staging workflow's name has " (STAGING)" appended; secret is identical
    id=$(sudo docker exec n8n n8n list:workflow 2>/dev/null \
      | grep -i "Cal.com Booking.*STAGING" | head -1 | awk -F'|' '{print $1}')
  else
    id="VMv0EOCNmDIbUvcf"
  fi
  if [ -z "$id" ]; then
    echo "ERROR: could not find Cal.com workflow id for env=$ENV" >&2
    exit 3
  fi
  sudo docker exec n8n n8n export:workflow --id="$id" --output=/tmp/calcom-secret-tmp.json >/dev/null
  sudo docker cp n8n:/tmp/calcom-secret-tmp.json /tmp/calcom-secret-tmp.json
  sudo chown "$USER" /tmp/calcom-secret-tmp.json
  jq -r '.[0].nodes[] | select(.name=="Verify Signature") | .parameters.jsCode' /tmp/calcom-secret-tmp.json \
    | sed -n "s/.*SIGNING_SECRET = '\(.*\)';/\1/p"
  rm -f /tmp/calcom-secret-tmp.json
}

post_calcom() {
  local label="$1" lead_type="$2" secret="$3"
  local body sig status
  body=$(calcom_payload "$lead_type" "$label")
  sig=$(printf '%s' "$body" | openssl dgst -sha256 -hmac "$secret" -hex | awk '{print $2}')
  status=$(curl -sS -o /dev/null -w "%{http_code}" \
    -X POST "$BASE/$CALCOM_PATH" \
    -H "Content-Type: application/json" \
    -H "X-Cal-Signature-256: $sig" \
    -d "$body")
  printf "  calcom        [%-15s] HTTP %s\n" "$label" "$status"
}

echo "=== smoke test against $ENV ($BASE) ==="
echo "Email prefix: ${EMAIL_PREFIX}@example.test"
echo

echo "[contact-intake]"
post_contact "default-pros"  ""
post_contact "prospect"      "prospect"
post_contact "vendor_partn"  "vendor_partner"
post_contact "recruiter"     "recruiter"
post_contact "other"         "other"
echo

echo "[calcom]"
secret=$(get_calcom_secret)
if [ -z "$secret" ]; then
  echo "  WARN: no signing secret found — skipping Cal.com tests"
else
  post_calcom "default-pros" ""              "$secret"
  post_calcom "prospect"     "prospect"      "$secret"
  post_calcom "vendor_partn" "vendor_partner" "$secret"
  post_calcom "recruiter"    "recruiter"     "$secret"
  post_calcom "other"        "other"         "$secret"
  unset secret
fi

echo
echo "Verification:"
echo "  - All HTTP responses should be 200."
echo "  - Open Notion DB ${BASE} → 5 contact-intake test rows + 5 calcom test rows"
echo "    (filter on Contact Email starts with '${EMAIL_PREFIX}-')."
echo "  - prospect/default rows: Status='New Lead' (contact) or 'Discovery Scheduled' (calcom),"
echo "    Lead Type='prospect'."
echo "  - vendor_partner/recruiter/other rows: Status='Disqualified', Lead Type matches."
echo "  - For contact-intake non-prospect: NO email should be sent (check inbox);"
echo "    Telegram should show '[lead-type filtered] <type>: ...' single line."
echo
echo "Cleanup: filter Notion by Contact Email starting with '${EMAIL_PREFIX}' and delete."
