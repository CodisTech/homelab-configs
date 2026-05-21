#!/usr/bin/env bash
# Deploy helper for CRL lead-type-filtering workflows.
#
# Usage (run on VM 100, from this directory):
#   ./deploy.sh stage      # imports/updates *.staging.json copies, activates
#   ./deploy.sh promote    # PUTs *.prod.json content over prod IDs, tears down stagings
#   ./deploy.sh rollback   # restores prod from $SNAPSHOT_DIR (taken at promote time)
#
# Why REST API for activate/delete/content-update: n8n 2.4.6 CLI has no
# delete:workflow, deprecates update:workflow --active=true, and import:workflow
# does not reliably overwrite existing workflow content (we observed it leaving
# pre-existing duplicate-name workflows untouched). PUT /api/v1/workflows/:id
# is the only reliable way to replace content.
#
# Secret handling: committed *.json files have the Cal.com signing secret redacted
# to "__CALCOM_WEBHOOK_SECRET__". This script reads the live secret from the
# running prod Cal.com workflow before each deploy and substitutes it back in.
set -euo pipefail

ACTION="${1:-}"
DIR="$(cd "$(dirname "$0")" && pwd)"
SNAPSHOT_DIR="$DIR/.snapshot"
N8N_URL="http://127.0.0.1:5678"

PROD_CONTACT_ID="RidzLH7xQ8WHLk9Q"
PROD_CALCOM_ID="VMv0EOCNmDIbUvcf"

STAGING_CONTACT_NAME="CRL: Contact Form → Lead Capture (STAGING)"
STAGING_CALCOM_NAME="CRL: Cal.com Booking → Lead Capture (STAGING)"

n8n_exec() { sudo docker exec n8n "$@" ; }
n8n_cp_out() { sudo docker cp "n8n:$1" "$2" && sudo chown "$USER" "$2" ; }
n8n_cp_in()  { sudo docker cp "$1" "n8n:$2" ; }

api_key() {
  sudo docker exec n8n printenv N8N_API_KEY
}

api_get() {
  local path="$1"
  curl -sf -H "X-N8N-API-KEY: $(api_key)" "$N8N_URL/api/v1/$path"
}

api_post_empty() {
  local path="$1"
  curl -sf -o /dev/null -X POST -H "X-N8N-API-KEY: $(api_key)" "$N8N_URL/api/v1/$path"
}

api_put_file() {
  local path="$1" file="$2"
  curl -sf -o /dev/null -X PUT \
    -H "X-N8N-API-KEY: $(api_key)" -H "Content-Type: application/json" \
    --data @"$file" "$N8N_URL/api/v1/$path"
}

api_delete() {
  local path="$1"
  curl -sf -o /dev/null -X DELETE -H "X-N8N-API-KEY: $(api_key)" "$N8N_URL/api/v1/$path"
}

# n8n 2.4.6 CLI list output is `<id>|<name>` — must split on '|', not whitespace.
list_workflow_id_by_name() {
  local name="$1"
  n8n_exec n8n list:workflow 2>/dev/null \
    | grep -F "$name" | head -1 | awk -F'|' '{print $1}'
}

activate_workflow()   { api_post_empty "workflows/$1/activate" ; }
deactivate_workflow() { api_post_empty "workflows/$1/deactivate" ; }
delete_workflow()     { api_delete "workflows/$1" ; }

# Convert a CLI-export-format workflow JSON ([{...}]) to public-API PUT format
# ({name, nodes, connections, settings}).
to_api_put_format() {
  local in="$1" out="$2"
  jq '.[0] | {name, nodes, connections, settings}' "$in" > "$out"
}

read_live_calcom_secret() {
  local tmp="/tmp/calcom-secret-read.json"
  n8n_exec n8n export:workflow --id="$PROD_CALCOM_ID" --output=/tmp/calcom-secret-read.json >/dev/null
  n8n_cp_out /tmp/calcom-secret-read.json "$tmp"
  n8n_exec rm -f /tmp/calcom-secret-read.json
  jq -r '.[0].nodes[] | select(.name=="Verify Signature") | .parameters.jsCode' "$tmp" \
    | sed -n "s/.*SIGNING_SECRET = '\(.*\)';/\1/p"
  rm -f "$tmp"
}

rehydrate_secret() {
  local f="$1" secret="$2"
  python3 -c "
import json, sys
fpath, secret = sys.argv[1], sys.argv[2]
with open(fpath) as h: d = json.load(h)
for n in d[0]['nodes']:
    if n.get('name') == 'Verify Signature' and 'jsCode' in (n.get('parameters') or {}):
        n['parameters']['jsCode'] = n['parameters']['jsCode'].replace('__CALCOM_WEBHOOK_SECRET__', secret)
with open(fpath, 'w') as h: json.dump(d, h, indent=2)
" "$f" "$secret"
}

stage() {
  echo "=== STAGE ==="
  local secret tmp
  secret="$(read_live_calcom_secret)"
  [ -n "$secret" ] || { echo "FATAL: could not read Cal.com signing secret" >&2 ; exit 4 ; }

  tmp="$(mktemp -d)"
  cp contact-form.staging.json "$tmp/contact-staging.json"
  cp calcom-booking.staging.json "$tmp/calcom-staging.json"
  rehydrate_secret "$tmp/calcom-staging.json" "$secret"

  for pair in \
    "contact-staging.json|$STAGING_CONTACT_NAME" \
    "calcom-staging.json|$STAGING_CALCOM_NAME" ; do
    local file="${pair%%|*}"
    local name="${pair#*|}"
    local id
    id="$(list_workflow_id_by_name "$name")"

    to_api_put_format "$tmp/$file" "$tmp/${file%.json}.put.json"

    if [ -n "$id" ]; then
      echo "  staging exists ($id), replacing content via PUT..."
      api_put_file "workflows/$id" "$tmp/${file%.json}.put.json"
    else
      echo "  creating new staging via import..."
      n8n_cp_in "$tmp/$file" "/tmp/import-$file"
      n8n_exec n8n import:workflow --input="/tmp/import-$file" 2>&1 | tail -1
      n8n_exec rm -f "/tmp/import-$file"
      id="$(list_workflow_id_by_name "$name")"
      [ -n "$id" ] || { echo "FATAL: post-import lookup failed for $name" >&2 ; exit 5 ; }
    fi

    activate_workflow "$id"
    echo "  $name -> $id (active)"
  done

  rm -rf "$tmp"
  echo "  done. Run ./smoke-test.sh staging next."
}

promote() {
  echo "=== PROMOTE ==="
  mkdir -p "$SNAPSHOT_DIR"
  local secret tmp
  secret="$(read_live_calcom_secret)"
  [ -n "$secret" ] || { echo "FATAL: missing live secret" >&2 ; exit 4 ; }

  echo "  snapshotting current production..."
  for id in "$PROD_CONTACT_ID" "$PROD_CALCOM_ID" ; do
    n8n_exec n8n export:workflow --id="$id" --output="/tmp/snap-$id.json" >/dev/null
    n8n_cp_out "/tmp/snap-$id.json" "$SNAPSHOT_DIR/$id.json"
    n8n_exec rm -f "/tmp/snap-$id.json"
  done

  tmp="$(mktemp -d)"
  cp contact-form.prod.json "$tmp/contact-prod.json"
  cp calcom-booking.prod.json "$tmp/calcom-prod.json"
  rehydrate_secret "$tmp/calcom-prod.json" "$secret"
  to_api_put_format "$tmp/contact-prod.json" "$tmp/contact-prod.put.json"
  to_api_put_format "$tmp/calcom-prod.json" "$tmp/calcom-prod.put.json"

  echo "  PUT prod contact-form ($PROD_CONTACT_ID)..."
  api_put_file "workflows/$PROD_CONTACT_ID" "$tmp/contact-prod.put.json"
  echo "  PUT prod calcom ($PROD_CALCOM_ID)..."
  api_put_file "workflows/$PROD_CALCOM_ID" "$tmp/calcom-prod.put.json"

  # PUT may flip active=false; reactivate explicitly.
  activate_workflow "$PROD_CONTACT_ID"
  activate_workflow "$PROD_CALCOM_ID"

  echo "  tearing down STAGING workflows..."
  for name in "$STAGING_CONTACT_NAME" "$STAGING_CALCOM_NAME" ; do
    local id
    id="$(list_workflow_id_by_name "$name")"
    if [ -n "$id" ]; then
      deactivate_workflow "$id" || true
      delete_workflow "$id"
      echo "    deleted $name -> $id"
    fi
  done

  rm -rf "$tmp"
  echo "  done. Snapshots at $SNAPSHOT_DIR/. Run ./smoke-test.sh production."
}

rollback() {
  echo "=== ROLLBACK from $SNAPSHOT_DIR ==="
  [ -d "$SNAPSHOT_DIR" ] || { echo "FATAL: no snapshot dir" >&2 ; exit 5 ; }
  local tmp; tmp="$(mktemp -d)"
  for f in "$SNAPSHOT_DIR"/*.json ; do
    local id
    id="$(jq -r '.[0].id' "$f")"
    [ -n "$id" ] && [ "$id" != "null" ] || { echo "  skip $f (no id)" ; continue ; }
    to_api_put_format "$f" "$tmp/$(basename "$f").put.json"
    echo "  restoring $id from $(basename "$f")..."
    api_put_file "workflows/$id" "$tmp/$(basename "$f").put.json"
    activate_workflow "$id" || true
  done
  rm -rf "$tmp"
  echo "  done."
}

case "$ACTION" in
  stage)    stage ;;
  promote)  promote ;;
  rollback) rollback ;;
  *) echo "usage: $0 stage|promote|rollback" >&2 ; exit 2 ;;
esac
