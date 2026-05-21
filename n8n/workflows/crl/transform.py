#!/usr/bin/env python3
"""
Transform CRL Contact Form + Cal.com Booking n8n workflows to add lead_type filtering.

Input: original workflow JSON exports.
Output: prod (modified, same ID/path) + staging (new ID, name+'(STAGING)', path+'-staging').

Run on VM 100 where the originals were exported. Idempotent — re-running on already-modified
JSONs is safe because we detect the marker node names.
"""
import json
import sys
import uuid
import argparse
import copy
import os
import re

NOTION_DB = "90720d68ecdf4be78ff76feddd9eff58"


def new_id() -> str:
    return str(uuid.uuid4())


def find_node(nodes, name):
    for n in nodes:
        if n.get("name") == name:
            return n
    return None


def transform_contact_form(wf: dict) -> dict:
    """
    Original topology:
      Contact Intake Webhook -> Extract Contact Data -> [Create Lead in Notion, Notify Telegram, Send Confirmation Email]

    New topology:
      Contact Intake Webhook -> Extract Contact Data -> Lead Type Gate (IF leadType==prospect)
        true  -> [Create Lead in Notion, Notify Telegram, Send Confirmation Email]   (existing prospect path)
        false -> [Create Disqualified Lead in Notion, Notify Telegram (light)]       (new branch)

    Existing "Create Lead in Notion" payload gains 'Lead Type': 'prospect'.
    """
    nodes = wf["nodes"]
    conns = wf["connections"]

    if find_node(nodes, "Lead Type Gate"):
        return wf  # already transformed

    extract = find_node(nodes, "Extract Contact Data")
    create_lead = find_node(nodes, "Create Lead in Notion")
    telegram = find_node(nodes, "Notify Telegram")
    email = find_node(nodes, "Send Confirmation Email")
    if not (extract and create_lead and telegram and email):
        raise RuntimeError("Contact Form: expected nodes missing")

    # 1. Add leadType field to Extract Contact Data.
    # Tally posts the dropdown answer as the friendly label string (free-tier
    # Tally has no separate label/value). Map known friendly labels to the
    # canonical snake_case values the gate expects. Unknown / missing -> prospect.
    leadtype_expr = (
        '={{ ({'
        '"I\'m interested in your security services": "prospect", '
        '"I\'m a vendor or partner": "vendor_partner", '
        '"I\'m a recruiter": "recruiter", '
        '"Something else": "other", '
        # canonical self-mappings — keeps smoke-test.sh (which sends snake_case
        # literals) working alongside real Tally/Cal.com which send friendly labels.
        '"prospect": "prospect", '
        '"vendor_partner": "vendor_partner", '
        '"recruiter": "recruiter", '
        '"other": "other"'
        "})[$json.body.data.lead_type || $json.body.data.leadType] || 'prospect' }}"
    )
    assigns = extract["parameters"]["assignments"]["assignments"]
    leadtype_existing = next((a for a in assigns if a["name"] == "leadType"), None)
    if leadtype_existing is None:
        assigns.append({
            "id": new_id(),
            "name": "leadType",
            "value": leadtype_expr,
            "type": "string",
        })
    else:
        leadtype_existing["value"] = leadtype_expr

    # 2. Patch existing Notion payload: add 'Lead Type': { select: { name: 'prospect' } }
    body = create_lead["parameters"].get("jsonBody", "")
    if "'Lead Type'" not in body:
        # insert a Lead Type select property into the JSON.stringify properties object
        body = body.replace(
            "'Source': { select: { name: 'Contact Form' } }",
            "'Source': { select: { name: 'Contact Form' } }, 'Lead Type': { select: { name: 'prospect' } }",
            1,
        )
        create_lead["parameters"]["jsonBody"] = body

    # 3. Position the new gate roughly between Extract and the fan-out
    ex_x, ex_y = extract["position"]
    gate_x, gate_y = ex_x + 220, ex_y

    # 4. Add Lead Type Gate IF node (boolean: leadType == 'prospect')
    gate = {
        "parameters": {
            "conditions": {
                "options": {
                    "version": 2,
                    "leftValue": "",
                    "caseSensitive": True,
                    "typeValidation": "loose",
                },
                "combinator": "and",
                "conditions": [{
                    "id": new_id(),
                    "leftValue": "={{ $json.leadType }}",
                    "rightValue": "prospect",
                    "operator": {"type": "string", "operation": "equals"},
                }],
            },
        },
        "id": new_id(),
        "name": "Lead Type Gate",
        "type": "n8n-nodes-base.if",
        "typeVersion": 2.2,
        "position": [gate_x, gate_y],
    }
    nodes.append(gate)

    # 5. Add Create Disqualified Lead in Notion (HTTP)
    disq_payload = (
        "={{ JSON.stringify({ "
        "parent: { database_id: '" + NOTION_DB + "' }, "
        "properties: { "
        "'Company Name': { title: [{ text: { content: $json.company || $json.fullName || $json.email } }] }, "
        "'Contact Email': { email: $json.email }, "
        "'Primary Contact': { rich_text: [{ text: { content: $json.fullName } }] }, "
        "'Source': { select: { name: 'Contact Form' } }, "
        "'Status': { select: { name: 'Disqualified' } }, "
        "'Lead Type': { select: { name: $json.leadType } }, "
        "'Start Date': { date: { start: $json.today } }, "
        "'Notes': { rich_text: [{ text: { content: 'Disqualified at intake. lead_type=' + $json.leadType + ' | role=' + ($json.role || '') + ' | driver=' + ($json.driver || '') } }] } "
        "} }) }}"
    )
    disq_notion = copy.deepcopy(create_lead)
    disq_notion["id"] = new_id()
    disq_notion["name"] = "Create Disqualified Lead in Notion"
    disq_notion["position"] = [gate_x + 240, gate_y + 200]
    disq_notion["parameters"]["jsonBody"] = disq_payload
    nodes.append(disq_notion)

    # 6. Add Notify Telegram (light) — single line, no formatting
    light_telegram = copy.deepcopy(telegram)
    light_telegram["id"] = new_id()
    light_telegram["name"] = "Notify Telegram (light)"
    light_telegram["position"] = [gate_x + 240, gate_y + 360]
    light_telegram["parameters"]["text"] = (
        "=[lead-type filtered] {{ $json.leadType }}: {{ $json.fullName }} <{{ $json.email }}>"
        " @ {{ $json.company }} | role={{ $json.role }}"
    )
    nodes.append(light_telegram)

    # 7. Set required emailSend params (n8n 2.4.6 emailSend v2.1 enforces these
    #    at activation; prod is grandfathered without them but new imports fail
    #    checkForWorkflowIssues unless fromEmail/toEmail/subject are present).
    email_params = email["parameters"]
    email_params.setdefault("fromEmail", "john@cyberreadylabs.com")
    email_params.setdefault("toEmail", "={{ $json.email }}")
    email_params.setdefault("subject", "Your CyberReadyLabs inquiry — next steps")

    # 8. Rewire: Extract -> Gate (replace Extract's main fan-out)
    conns["Extract Contact Data"] = {
        "main": [[{"node": "Lead Type Gate", "type": "main", "index": 0}]]
    }
    # Gate true (output 0) -> existing fan-out; Gate false (output 1) -> disqualified branch
    conns["Lead Type Gate"] = {
        "main": [
            [
                {"node": "Create Lead in Notion", "type": "main", "index": 0},
                {"node": "Notify Telegram", "type": "main", "index": 0},
                {"node": "Send Confirmation Email", "type": "main", "index": 0},
            ],
            [
                {"node": "Create Disqualified Lead in Notion", "type": "main", "index": 0},
                {"node": "Notify Telegram (light)", "type": "main", "index": 0},
            ],
        ]
    }

    return wf


def transform_calcom(wf: dict) -> dict:
    """
    Minimal change: in Extract Booking Data, add leadType + override notionStatus when
    leadType != 'prospect'. In all 3 Notion HTTP bodies, add Lead Type property.
    Also: adjust the Telegram message for non-prospect bookings.
    """
    nodes = wf["nodes"]

    extract = find_node(nodes, "Extract Booking Data")
    update_lead = find_node(nodes, "Update Existing Lead")
    create_lead = find_node(nodes, "Create New Lead")
    telegram = find_node(nodes, "Notify Telegram")
    if not (extract and update_lead and create_lead and telegram):
        raise RuntimeError("Cal.com: expected nodes missing")

    # 1. Add leadType extraction (Cal.com puts custom-field answers in payload.responses
    #    keyed by field label OR slug, or in userFieldsResponses array).
    # The Cal.com Booking Question stores one string per option (no separate
    # label/value), so the answer arrives as the friendly label string. Wrap
    # the extraction with a lookup that maps known friendly labels to the
    # canonical snake_case values the gate expects. Unknown / missing -> prospect.
    # NOTE: n8n Set v3.x evaluates all assignments in parallel against the input.
    # Other assignments in the same Set node CANNOT reference $json.leadType —
    # it would always read undefined. The full body is reused inline below.
    extraction = (
        "($json.body.payload.responses && "
        "($json.body.payload.responses.lead_type?.value "
        "|| $json.body.payload.responses['Lead Type']?.value)) "
        "|| ($json.body.payload.userFieldsResponses && "
        "$json.body.payload.userFieldsResponses.find(r => "
        "(r.label === 'Lead Type' || r.label === 'lead_type'))?.value)"
    )
    leadtype_map = (
        '({'
        '"I\'m interested in your security services": "prospect", '
        '"I\'m a vendor or partner": "vendor_partner", '
        '"I\'m a recruiter": "recruiter", '
        '"Something else": "other", '
        # canonical self-mappings (smoke-test.sh sends snake_case literals).
        '"prospect": "prospect", '
        '"vendor_partner": "vendor_partner", '
        '"recruiter": "recruiter", '
        '"other": "other"'
        '})'
    )
    leadtype_body = leadtype_map + "[" + extraction + "] || 'prospect'"
    leadtype_expr = "={{ " + leadtype_body + " }}"

    assigns = extract["parameters"]["assignments"]["assignments"]
    leadtype_existing = next((a for a in assigns if a["name"] == "leadType"), None)
    if leadtype_existing is None:
        assigns.append({
            "id": new_id(),
            "name": "leadType",
            "value": leadtype_expr,
            "type": "string",
        })
    else:
        leadtype_existing["value"] = leadtype_expr

    # 2. Override notionStatus for non-prospect. Inline the leadType extraction
    #    instead of referencing $json.leadType (parallel-eval limitation above).
    expr_re = re.compile(r"^=\{\{\s*(.*?)\s*\}\}$", re.DOTALL)
    for a in assigns:
        if a["name"] == "notionStatus":
            original = a["value"]
            if "Disqualified" not in original:
                m = expr_re.match(original)
                inner = m.group(1) if m else original
                a["value"] = (
                    "={{ ((" + leadtype_body + ") !== 'prospect') ? 'Disqualified' : "
                    "(" + inner + ") }}"
                )

    # 3. Patch the 3 Notion HTTP bodies to add Lead Type property.
    #    Existing bodies use the pattern 'Status': { select: { name: ... } }
    def add_lead_type(body: str, lead_expr: str) -> str:
        if "'Lead Type'" in body:
            return body
        # insert right after the Status property
        return re.sub(
            r"('Status':\s*\{\s*select:\s*\{\s*name:[^}]+\}\s*\})",
            r"\1, 'Lead Type': { select: { name: " + lead_expr + " } }",
            body,
            count=1,
        )

    # Find Existing Lead query body — no need to add Lead Type to query
    update_body = update_lead["parameters"].get("jsonBody", "")
    update_lead["parameters"]["jsonBody"] = add_lead_type(
        update_body, "$('Extract Booking Data').item.json.leadType"
    )
    create_body = create_lead["parameters"].get("jsonBody", "")
    create_lead["parameters"]["jsonBody"] = add_lead_type(
        create_body, "$('Extract Booking Data').item.json.leadType"
    )

    # 4. Telegram: append a [lead-type filtered] line for non-prospect.
    #    Easiest: prepend a conditional banner to the existing text.
    text = telegram["parameters"].get("text", "")
    if "[lead-type filtered]" not in text:
        # prepend a one-line non-prospect banner
        banner = (
            "={{ $('Extract Booking Data').item.json.leadType !== 'prospect' "
            "? '[lead-type filtered] ' + $('Extract Booking Data').item.json.leadType + '\\n\\n' : '' }}"
        )
        # text already starts with '=' (n8n expression). Strip the leading '=', concat, re-prefix.
        body = text.lstrip("=")
        telegram["parameters"]["text"] = banner.lstrip("=") + body
        telegram["parameters"]["text"] = "=" + telegram["parameters"]["text"].lstrip("=")
        # Re-prepend = if missing
        if not telegram["parameters"]["text"].startswith("="):
            telegram["parameters"]["text"] = "=" + telegram["parameters"]["text"]

    return wf


def make_staging_copy(wf: dict, suffix: str = "-staging") -> dict:
    """Produce a staging variant: clear ID, append (STAGING) to name, suffix webhook path."""
    s = copy.deepcopy(wf)
    s.pop("id", None)
    s.pop("versionId", None)
    s.pop("activeVersionId", None)
    s["name"] = s["name"] + " (STAGING)"
    for n in s["nodes"]:
        if n.get("type") == "n8n-nodes-base.webhook":
            old_path = n["parameters"].get("path", "")
            if not old_path.endswith(suffix):
                n["parameters"]["path"] = old_path + suffix
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    os.makedirs(args.out_dir, exist_ok=True)

    transforms = {
        "RidzLH7xQ8WHLk9Q.json": ("contact-form", transform_contact_form),
        "VMv0EOCNmDIbUvcf.json": ("calcom-booking", transform_calcom),
    }

    for fname, (slug, fn) in transforms.items():
        with open(os.path.join(args.in_dir, fname)) as f:
            doc = json.load(f)
        wf = doc[0]
        prod = fn(copy.deepcopy(wf))
        staging = make_staging_copy(prod)
        with open(os.path.join(args.out_dir, f"{slug}.prod.json"), "w") as f:
            json.dump([prod], f, indent=2)
        with open(os.path.join(args.out_dir, f"{slug}.staging.json"), "w") as f:
            json.dump([staging], f, indent=2)
        print(f"  {slug}: wrote prod + staging")


if __name__ == "__main__":
    main()
