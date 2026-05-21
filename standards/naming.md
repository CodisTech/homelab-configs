# Naming Convention

**Last updated**: 2026-05-14
**Status**: ACTIVE — applies to all new VMs/LXC. Existing workloads are renamed during natural lifecycle events (rebuild, migration, scheduled maintenance) per `planning/inventory.csv` — see `target_name` column.

---

## Format

```
<tier>-<purpose>-<node>-<instance>
```

| Segment | Format | Examples |
|---|---|---|
| `<tier>` | lowercase, matches resource pool name | `prod`, `infra`, `security`, `network`, `k3s`, `exp`, `fw`, `storage` |
| `<purpose>` | short descriptor, kebab-case, NO redundant words | `web`, `services`, `unifi`, `claude`, `haos`, `cp`, `worker`, `opnsense` |
| `<node>` | single letter A/B/C/D for the Proxmox host | `a`, `b`, `c`, `d` |
| `<instance>` | zero-padded 2-digit `NN` starting at 01 | `01`, `02`, `03` |

### Rules

1. **All lowercase**, hyphens between segments, no underscores or camelCase.
2. **No version numbers in the name** — version is on the image tag, not the VM name. Bad: `k3s-control-v2`. Good: `k3s-cp-a`.
3. **No environment suffixes** — `crl-prod-web-c-01` already encodes prod via tier. Don't add `-prod` redundantly.
4. **Special CP/worker exception for k3s**: `k3s-cp-<node>` (no instance number — only one CP per node) and `k3s-worker-<node>-<NN>` (multiple workers per node allowed).
5. **Firewall exception**: `fw-opnsense-<node>-<role>` where role = `primary` or `secondary` (CARP role, not instance).
6. **Storage exception**: `storage-truenas-<node>-<NN>` — node letter for the host the TrueNAS VM lives on.

---

## Tier model (6 + firewall)

| Tier | Pool name | VLAN | Examples |
|---|---|---|---|
| 1. Production | `prod-crl` | 70 | `crl-prod-web-c-01`, future Stripe/Cal.com webhook receivers |
| 2. Core Infra | `infra-core` | 60 | `infra-services-c-01` (Docker host), `infra-claude-a-01`, `infra-haos-c-01` |
| 3. Security | `infra-security` | 60 (today) → consider dedicated VLAN later | `security-suricata-c-01`, future Wazuh-on-k3s migration target |
| 4. Network | `infra-network` | 60 management | `network-unifi-c-01`, future OPNsense mgmt-plane VMs |
| 5. Kubernetes | `k3s` | 60 currently | `k3s-cp-a`, `k3s-cp-b`, `k3s-cp-c`, `k3s-worker-a-01`, `k3s-worker-c-02` |
| 6. Experiments | `experiments` | (carve from 40 or new) | `exp-minecraft-a-01`, throwaway test VMs |
| Separate: Firewall | n/a | n/a | `fw-opnsense-d-primary`, `fw-opnsense-c-secondary` |
| Separate: Storage | n/a | n/a | `storage-truenas-b-01` |

**Why firewall + storage are outside the 4-app-tier model**: they're foundational infrastructure that everything else depends on. Putting them in a pool with workload VMs incorrectly suggests they're peers. They are not — losing the firewall takes the whole homelab down; losing the NAS strands every app.

---

## Examples — current vs. renamed

(See `planning/inventory.csv` for the full mapping. Sample below.)

| Current | Renamed to | Tier |
|---|---|---|
| `claude-code-host` | `infra-claude-a-01` | infra-core |
| `ubuntuserver22` | `infra-services-c-01` | infra-core |
| `UnifiOS` | `network-unifi-c-01` | infra-network |
| `cyberreadylabs` | `crl-prod-web-c-01` | prod-crl |
| `suricata` | `security-suricata-c-01` | infra-security |
| `haos` | `infra-haos-c-01` | infra-core |
| `opnsense-1` | `fw-opnsense-c-secondary` | firewall |
| `opnsense-dell` | `fw-opnsense-d-primary` | firewall |
| `k3s-control` → rebuild | `k3s-cp-a` (Talos) | k3s |
| `k3s-worker-1` → rebuild | `k3s-worker-a-01` (Talos) | k3s |

---

## When to rename

Renames touch active production. Don't rename during business hours.

- **Stage 0 (paperwork-only)**: this file documents the convention. NO VMs are renamed yet.
- **Stage 6 (Talos rebuild)**: new VMs get correct names from the start; old `k3s-control/worker-N` are decommissioned. No mid-life rename needed.
- **Stage 4 (OPNsense Dell rebuild)**: new `fw-opnsense-d-primary` built fresh on Dell. Existing `opnsense-1` renamed to `fw-opnsense-c-secondary` during Stage 4 Session 4 (the CARP pairing session — already taking that VM offline briefly).
- **Other live VMs** (`claude-code-host`, `ubuntuserver22`, `UnifiOS`, `cyberreadylabs`, `suricata`, `haos`): rename during the next scheduled maintenance window for that VM. `qm set <vmid> --name <newname>` is non-disruptive (no reboot required) but the change is most useful as part of a Proxmox-cluster-formation event (Stage 3) where the resource pool assignment also happens.

---

## Resource pools (Stage 0 deliverable, Proxmox UI)

Create pools matching the tier names:
- `prod-crl`
- `infra-core`
- `infra-security`
- `infra-network`
- `k3s`
- `experiments`

Firewall + storage VMs do NOT get pools — they sit at the cluster level as "infrastructure" by convention. Visible in the Proxmox UI alongside the pooled VMs but un-grouped.

Resource pools have no operational effect on VMs (no resource limits, no scheduling impact). They're purely organizational labels in the Proxmox UI.

---

## Special cases & exceptions

| VM | Reason | Convention exception |
|---|---|---|
| `claude-code-host` | Active utility VM the user drives sessions from | Renamed to `infra-claude-a-01`. If a future iteration restores it as a one-off named VM, can keep `claude-code-host` and document here. |
| Cloud-init/cluster templates | Templates aren't deployed VMs | Suffix `-template` is fine: `k3s-worker-template`, `talos-cp-template` |
| TrueNAS VM | Storage is a foundational tier outside the 4-app-tier model | `storage-truenas-b-01` — uses `storage-` prefix |
| Postgres DB VMs (if any future) | Database is shared infra | Tier = `infra-core`, purpose = `postgres`: `infra-postgres-c-01` |

---

## Hostname vs. VM name

Proxmox VM name (what shows in the UI) is independent of the guest OS hostname. The convention here applies to the **Proxmox VM name**. Guest OS hostname can differ but should align — e.g., guest `infra-haos-c-01.local` matches VM name `infra-haos-c-01`.

Existing exception: PVE host C currently has hostname `nas` (legacy). Rename to `pve-server-c` is tracked in `project_pve_c_rename.md` — pair with SSH hardening window.
