# VLAN Map

**Last updated**: 2026-05-14
**Status**: Inventory of CURRENT state + intended TARGET state. The migration to target state happens in Stage 3 of the Reorganization Plan (`00_Dashboard/Reorganization_Plan.md` in the vault).

OPNsense rule export is at `network/opnsense-rules.md` (TODO — pull a current snapshot before Stage 3 VLAN changes).

---

## Current VLAN assignments (from `qm config <vmid>` pulls 2026-05-14)

| VM | Host | Bridge | VLAN tag | Notes |
|---|---|---|---|---|
| claude-code-host | A | vmbr0 | untagged | Defaults to whatever vmbr0 native is on A |
| k3s-control | A | vmbr0 | untagged | Same |
| k3s-worker-1 | A | vmbr0 | untagged | Same |
| ubuntuserver22 (VM 100) | C | vmbr0 | untagged | Big Docker host — Pi-hole, monitoring, n8n, Nextcloud |
| UnifiOS | C | vmbr1 | **40** | UniFi controller — already on a dedicated VLAN |
| opnsense-1 | C | vmbr3 | (WAN/transit bridge) | Firewall — own bridge |
| opnsense-2 | C | vmbr3 | (WAN/transit bridge) | Stopped; dead failover |
| cyberreadylabs | C | vmbr1 | **70** | Production CRL — already on prod VLAN |
| suricata | C | vmbr1 | **60** | IDS |
| haos | C | vmbr0 | untagged | Home Assistant |
| k3s-worker-2 | C | vmbr0 | untagged | Inconsistent with worker-3 |
| k3s-worker-3 | C | vmbr1 | **60** | Inconsistent with worker-2 |
| k3s-worker-template | C | vmbr1 | **60** | Template |
| opnsense-dell | D | vmbr2 | trunks=1-4094 | Stopped; trunk port for Dell rebuild |

**Inconsistencies to fix**:
1. k3s workers split across `vmbr0` and `vmbr1` with different tagging — pick one and align.
2. Several "production-grade" VMs (haos, ubuntuserver22) on untagged vmbr0 — should be on a tagged VLAN.
3. `vmbr3` is opnsense-only on C — fine for the active firewall, but post-Dell-rebuild this bridge becomes redundant.

---

## Existing VLAN inventory (OPNsense interfaces, from CLAUDE.md + memory)

| VLAN | Name | Subnet | Purpose |
|---|---|---|---|
| 10 | ADMIN | 10.0.10.0/24 | Admin management plane |
| 20 | (legacy) | - | (unused or limited use; verify) |
| 30 | TRUSTED | 10.0.30.0/24 | Admin user access |
| 40 | (network mgmt) | 10.0.40.0/24 | Network device mgmt (UniFi sits here) |
| 50 | (unused/legacy) | - | (verify) |
| 60 | SERVICES | 10.0.60.0/24 | Internal services (most VMs live here) |
| 70 | PROD | 10.0.70.0/24 | CRL production |
| 80 | SECURITY | 10.0.80.0/24 | Vault infrastructure (per HA plan) |
| 90 | CEPH | 10.0.90.0/24 | Ceph cluster traffic (Ceph plan deprecated; VLAN can be repurposed for replication traffic) |
| 99 | SYNC | 10.0.99.0/24 | OPNsense HA sync (CARP) |

---

## Target state (per Reorganization Plan tier model)

| Tier | VLAN | Subnet | VMs going here |
|---|---|---|---|
| `prod-crl` | **70** | 10.0.70.0/24 | crl-prod-web-c-01 (existing), crl-prod-web-b-01-replica (Stage 8) |
| `infra-core` | **60** | 10.0.60.0/24 | infra-services-c-01, infra-claude-a-01, infra-haos-c-01 |
| `infra-security` | **60** today → consider dedicated VLAN later | 10.0.60.0/24 | security-suricata-c-01 |
| `infra-network` | **40** | 10.0.40.0/24 | network-unifi-c-01 |
| `k3s` | **60** | 10.0.60.0/24 | All Talos CPs + workers |
| `experiments` | carve from **40** or new VLAN **50** | - | Throwaway/dev VMs |
| `firewall` | n/a (bridges/transit) | - | fw-opnsense-d-primary, fw-opnsense-c-secondary |
| `storage` | **60** primary, dedicated storage VLAN later | 10.0.60.0/24 | storage-truenas-b-01 (Stage 2a) |

### Decisions deferred

- **Should infra-security get its own VLAN?** Real isolation argues yes. Today it's co-located on VLAN 60 with everything else. Revisit when Wazuh moves to k3s and the security stack grows.
- **Storage VLAN** — current plan has TrueNAS NFS serving k3s on VLAN 60. A dedicated storage VLAN with the 10 GbE direct A↔B link as its own subnet (no router involvement) would be the durable answer. Defer to Stage 6 (Talos rebuild) when the storage path gets re-evaluated.
- **experiments VLAN** — VLAN 50 was originally for "unused". Repurpose for experiments. Confirm before assigning.

---

## OPNsense rules (target intent)

Per Reorganization Plan Stage 3:

- `prod-crl` (VLAN 70) → outbound only via Cloudflare Tunnel; inbound from `infra-core` (DNS, SSO) only
- `infra-core` (VLAN 60) → reachable by all tiers (it's shared infra)
- `infra-security` → mostly outbound (alerts to Telegram); inbound only from `infra-core` (Wazuh manager → agent comms) and the IDS span port
- `infra-network` → out-of-band management; tightly restricted
- `k3s` → can reach `infra-core` + `infra-security` for agents; explicit allowlist for anything else
- `experiments` → permissive but logged; logs go to Loki
- `firewall` mgmt → only from `infra-network` (VLAN 40) admin hosts
- `storage` → only NFS/SMB ports open; egress denied except for updates

Rule export from current OPNsense → `network/opnsense-rules.md` is TODO (pre-Stage 3).

---

## Migration steps (Stage 3 plan reference)

1. Add the missing VLAN interfaces on OPNsense if not present (50 for experiments, dedicated security if approved)
2. Configure proper trunk ports on Proxmox bridges (`vmbr1` should trunk all tier VLANs, not just 40+60+70)
3. Re-tag each VM's `net0` per target table above via `qm set <vmid> --net0 ...`
4. Update OPNsense firewall rules to match tier-isolation intent
5. Test cross-tier connectivity per the rule matrix
6. Commit final OPNsense rule export to `network/opnsense-rules.md`

**Constraint**: rules edits go via OPNsense GUI — `config.xml` direct edits break DHCP. See `feedback_opnsense_no_sed.md`.
