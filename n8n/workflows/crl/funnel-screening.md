# Funnel screening — vendor / recruiter / other filtering

## Why

Until 2026-05-08 every Cal.com booking and Tally `/webhook/contact-intake` submission was treated as a prospect: full Notion CRM record, branded confirmation email, full-format Telegram alert. A vendor or recruiter slipping into the funnel polluted CRM data and burned a discovery slot.

This adds a `lead_type` qualifier upstream and routes accordingly:

- `prospect` (default if missing) — unchanged behavior
- `vendor_partner` / `recruiter` / `other` — record is still captured in Notion (audit trail) but tagged `Status='Disqualified'` with `Lead Type=<reason>`, the branded prospect email is suppressed, and Telegram drops to a single `[lead-type filtered] …` line

## Affected workflows

| Workflow ID | Name | Path | Modified |
|---|---|---|---|
| `RidzLH7xQ8WHLk9Q` | CRL: Contact Form → Lead Capture | `/webhook/contact-intake` | yes |
| `VMv0EOCNmDIbUvcf` | CRL: Cal.com Booking → Lead Capture | `/webhook/calcom-x7kP9mR3vL2nQ8wF` | yes |
| `4U9hvcQS0OSAfkL4iNqMi` | CRL: Assessment Lead Capture → Notion | `/webhook/assessment-lead` | **not touched** (out of scope) |
| `puzhKHfg1lPQ5mdjC3gng` | CRL: Tally Intake → Notion | `/webhook/tally-intake` | **not touched** (different form, post-engagement) |

## What the modified workflows do

### Contact Form

Topology becomes: `Webhook → Extract Contact Data → Lead Type Gate (IF) → [prospect path | disqualified path]`

- `Lead Type Gate` is an n8n IF node testing `leadType === 'prospect'`.
- **Prospect path** (gate true): existing fan-out — Create Lead in Notion (now also writes `Lead Type='prospect'`) + Notify Telegram + Send Confirmation Email (the branded HTML).
- **Disqualified path** (gate false): `Create Disqualified Lead in Notion` (new HTTP node, `Status='Disqualified'`, `Lead Type=<value>`) + `Notify Telegram (light)` (new node, single line).
- The branded confirmation email is **only sent on the prospect path**.

### Cal.com Booking

Topology unchanged. Three small changes inside `Extract Booking Data` and the three Notion HTTP bodies:

- New field `leadType` extracted from `payload.responses.lead_type.value` / `payload.responses['Lead Type'].value` / `payload.userFieldsResponses[*]` (multi-shape fallback). Defaults `'prospect'`.
- `notionStatus` is now `'Disqualified'` whenever `leadType !== 'prospect'`; otherwise the existing trigger-event ternary is preserved.
- All three Notion payloads (Find/Update/Create) include `'Lead Type': { select: { name: <leadType> } }`.
- Telegram message gains a conditional one-line banner: `[lead-type filtered] <type>` when non-prospect; otherwise unchanged.

The find-or-create UPSERT in the Cal.com workflow already handles vendor reschedules / cancels correctly without further branching.

## Manual UI work — required after the n8n workflows promote to prod

These cannot be automated. Without them, every payload still defaults to `prospect` (backward compatible by design — the n8n changes are inert until `lead_type` arrives in payloads).

### 1. Notion DB `90720d68ecdf4be78ff76feddd9eff58`

- **Add a `Lead Type` select property** with options:
  - `prospect`
  - `vendor_partner`
  - `recruiter`
  - `other`
- **Add `Disqualified` to the existing `Status` select** options (single value; reason carried by `Lead Type`).

### 2. Tally form (front-door contact form on `cyberreadylabs.com`)

- Add a required dropdown question — text suggestion:
  > **What brings you to CyberReadyLabs?**
  > a) Evaluating services for my organization
  > b) Vendor / partnership inquiry
  > c) Recruiter / job opportunity
  > d) Other
- In the Tally webhook config, map this question's stable key to **`lead_type`**. The values posted to n8n must be exactly: `prospect`, `vendor_partner`, `recruiter`, `other`. (Map answer (a) → `prospect`, (b) → `vendor_partner`, etc. Tally lets you set the value separately from the display label per option.)

### 3. Cal.com — `/15min` event type

- Open the event type → Booking Questions
- Add a new required dropdown question titled `Lead Type` with the same four options as Tally
- Map answer values (a)→`prospect`, (b)→`vendor_partner`, (c)→`recruiter`, (d)→`other`
- Cal.com posts the answer in `payload.responses.lead_type.value` (or `payload.responses['Lead Type'].value` depending on field key vs label) — the n8n workflow's extraction handles both shapes.

## Deployment / promotion

This change is shipped via two-step deploy (because there is no second n8n staging instance):

1. **Stage:** import a `(STAGING)` copy of each modified workflow with webhook path suffixed `-staging`. Both staging + production workflows run in parallel; staging consumes only smoke-test traffic.
2. **Smoke test** (see `scripts/test/smoke-test.sh`): 5 cases per webhook (default-prospect, prospect, vendor_partner, recruiter, other). Confirm Notion records, no prospect email on disqualified, light Telegram on disqualified.
3. **Promote:** import the production-id versions (overwrites by ID), deactivate stagings, delete staging copies.
4. **Manual UI work** in Tally / Cal.com / Notion happens after promotion. Default-`prospect` until then keeps existing flow intact.

## Rollback

`deploy.sh promote` snapshots the live production workflows into `.snapshot/<id>.json` (gitignored) before overwriting. To roll back: `./deploy.sh rollback`.

Alternatively, n8n's `workflow_history` table preserves prior versions; revert via the n8n editor UI under Workflow → Versions.

## Secret hygiene

The Cal.com webhook signing secret lives in the `Verify Signature` node's `jsCode` as a JS literal. Committed copies of `calcom-booking.{prod,staging}.json` redact it to `__CALCOM_WEBHOOK_SECRET__` because this repo mirrors to public GitHub. `deploy.sh` reads the live secret from the running production workflow before each import and substitutes it back. If the production workflow is unavailable when running `deploy.sh stage` (cold-start scenario), recover the secret from the Cal.com webhook config UI or n8n's `workflow_history` table.

## Out-of-scope but related

- The `assessment-lead` workflow (post-assessment results email) is intentionally untouched — that endpoint isn't a discovery-call funnel and screening it doesn't add value.
- `tally-intake` is a different Tally form for post-engagement intake, also untouched.
- Future: the `Lead Type` property could feed the Francis daily digest as a "today's filtered leads" signal so vendors aren't entirely invisible.
