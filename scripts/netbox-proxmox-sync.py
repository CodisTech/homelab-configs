#!/usr/bin/env python3
"""
netbox-proxmox-sync.py — Mirror live PVE VM state into NetBox.

Closes the drift loop: when you `qm set --name newname` or change CPU/RAM
on a Proxmox host, NetBox reflects the change within minutes (or whenever
the systemd timer next fires). Without this, NetBox slowly diverges from
reality and stops being trustworthy as source-of-truth.

Behavior:
  - SSH to each PVE host as serveradmin (key auth, NOPASSWD sudo).
  - `qm list` + `qm config <vmid>` to pull live VM state (name, status,
    cores, memory in MB, and the bridge/tag from net0).
  - Compare against NetBox /virtualization/virtual-machines/ for the
    pve-cluster cluster.
  - For each PVE VM:
      - If a NetBox VM with the same name exists: PATCH vcpus/memory/
        status/device only if changed. Don't touch interfaces/IPs (manual).
      - If absent: POST a new VM linked to the cluster + device, with
        comments noting "<host>:<vmid> auto-discovered <date>".
  - List "stranded" NetBox VMs (in NetBox but not in any PVE qm output)
    so renames + retires are visible. Don't auto-delete — that's a manual
    decision.

Designed to run from a systemd user timer on VM 108, like n8n-workflow-export.

Match-by-name v1 limitation:
  Renames in PVE will surface as "create new + strand old." That's intentionally
  noisy so the human sees it. Future enhancement: store PVE vmid in a NetBox
  custom field for stable match.
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path
import urllib3
import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ----------------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------------
NB = os.environ.get("NB_URL", "https://netbox.home.example.home/api")
TOKEN = os.environ.get("NB_TOKEN")
SITE_ID = int(os.environ.get("NB_SITE_ID", "1"))      # 1 = Homelab
CLUSTER_NAME = os.environ.get("NB_CLUSTER", "pve-cluster")
DRY_RUN = os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")

# host_name_in_netbox -> (ip, alt_name_if_renamed)
# pve-server-c is still hostname "nas" until the deferred rename lands.
PVE_HOSTS = [
    ("pve-server-a", "10.0.60.10"),
    ("pve-server-c", "10.0.60.9"),
    ("pve-server-d", "10.0.60.8"),
]

SSH_OPTS = ["-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
            "-o", "StrictHostKeyChecking=no"]

# ----------------------------------------------------------------------------

S = requests.Session()
S.verify = False


def log(msg: str) -> None:
    print(msg, flush=True)


def ssh_run(ip: str, cmd: str) -> str:
    return subprocess.run(
        ["ssh", *SSH_OPTS, f"serveradmin@{ip}", cmd],
        capture_output=True, text=True, check=True,
    ).stdout


def pve_pull(host_name: str, ip: str) -> list[dict]:
    """Return list of {vmid, name, status, cores, memory_mb, bridge, vlan}."""
    out = ssh_run(ip, "sudo -n qm list")
    vms = []
    # Skip header line
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 4:
            continue
        vmid, name, status = parts[0], parts[1], parts[2]
        # qm config <vmid> emits 'key: value' lines
        cfg = ssh_run(ip, f"sudo -n qm config {vmid}")
        cores = _re_int(cfg, r"^cores:\s*(\d+)")
        sockets = _re_int(cfg, r"^sockets:\s*(\d+)") or 1
        memory = _re_int(cfg, r"^memory:\s*(\d+)")
        net0 = re.search(r"^net0:\s*(.+)$", cfg, re.M)
        bridge, vlan = None, None
        if net0:
            mb = re.search(r"bridge=(\S+)", net0.group(1))
            mt = re.search(r"tag=(\d+)", net0.group(1))
            bridge = mb.group(1).rstrip(",") if mb else None
            vlan = int(mt.group(1)) if mt else None
        vms.append({
            "vmid": int(vmid),
            "name": name,
            "status": status,
            "cores": (cores or 1) * sockets,
            "memory_mb": memory,
            "bridge": bridge,
            "vlan": vlan,
            "pve_host": host_name,
        })
    return vms


def _re_int(s: str, pattern: str) -> int | None:
    m = re.search(pattern, s, re.M)
    return int(m.group(1)) if m else None


# ----------------------------------------------------------------------------
# NetBox helpers
# ----------------------------------------------------------------------------

def nb_get_cluster_id() -> int:
    r = S.get(f"{NB}/virtualization/clusters/", params={"name": CLUSTER_NAME})
    r.raise_for_status()
    rs = r.json()["results"]
    if not rs:
        raise SystemExit(f"NetBox: no cluster named {CLUSTER_NAME!r}")
    return rs[0]["id"]


def nb_get_device_id(name: str) -> int | None:
    r = S.get(f"{NB}/dcim/devices/", params={"name": name})
    r.raise_for_status()
    rs = r.json()["results"]
    return rs[0]["id"] if rs else None


def nb_get_vms_by_cluster(cluster_id: int) -> dict[str, dict]:
    """Returns {name: vm}. Paginates the API."""
    out = {}
    url = f"{NB}/virtualization/virtual-machines/?cluster_id={cluster_id}&limit=200"
    while url:
        r = S.get(url)
        r.raise_for_status()
        data = r.json()
        for v in data["results"]:
            out[v["name"]] = v
        url = data.get("next")
    return out


def _status_val(field):
    """NetBox status fields come back as {'value': 'active', 'label': 'Active'}.
    Normalize to the string value for comparison."""
    if isinstance(field, dict):
        return field.get("value")
    return field


def _id_val(field):
    """Foreign-key fields come back as {'id': N, ...}. Normalize to id."""
    if isinstance(field, dict):
        return field.get("id")
    return field


# ----------------------------------------------------------------------------
# Sync core
# ----------------------------------------------------------------------------

def main() -> int:
    if not TOKEN:
        log("ERROR: NB_TOKEN env var not set")
        return 2
    S.headers["Authorization"] = f"Token {TOKEN}"
    S.headers["Content-Type"] = "application/json"

    cluster_id = nb_get_cluster_id()
    nb_vms = nb_get_vms_by_cluster(cluster_id)
    log(f"NetBox: cluster_id={cluster_id}, {len(nb_vms)} VMs in NetBox today")

    created, updated, unchanged, stranded = [], [], [], []
    seen_names: set[str] = set()

    for host_name, ip in PVE_HOSTS:
        device_id = nb_get_device_id(host_name)
        if device_id is None:
            log(f"WARN: no NetBox Device for {host_name!r} — skipping host")
            continue

        try:
            vms = pve_pull(host_name, ip)
        except subprocess.CalledProcessError as e:
            log(f"ERR: ssh/qm failed on {host_name} ({ip}): {e.stderr.strip()[:200]}")
            continue

        log(f"PVE {host_name}: {len(vms)} VMs live")

        for vm in vms:
            seen_names.add(vm["name"])
            nb_status = "active" if vm["status"] == "running" else "offline"
            target = {
                "vcpus": vm["cores"],
                "memory": vm["memory_mb"],
                "status": nb_status,
                "device": device_id,
            }

            existing = nb_vms.get(vm["name"])
            if existing:
                diffs = {}
                for k, v in target.items():
                    cur = existing.get(k)
                    if k == "status":
                        cur = _status_val(cur)
                    elif k == "device":
                        cur = _id_val(cur)
                    if cur != v and v is not None:
                        diffs[k] = v
                if diffs:
                    log(f"  ~ {vm['name']} (vmid {vm['vmid']}): {diffs}")
                    if not DRY_RUN:
                        r = S.patch(f"{NB}/virtualization/virtual-machines/{existing['id']}/", json=diffs)
                        r.raise_for_status()
                    updated.append((vm["name"], diffs))
                else:
                    unchanged.append(vm["name"])
            else:
                payload = {
                    "name": vm["name"],
                    "cluster": cluster_id,
                    "site": SITE_ID,
                    **target,
                    "comments": f"Auto-discovered from {host_name}:{vm['vmid']} via netbox-proxmox-sync",
                }
                log(f"  + {vm['name']} (vmid {vm['vmid']}, on {host_name})")
                if not DRY_RUN:
                    r = S.post(f"{NB}/virtualization/virtual-machines/", json=payload)
                    if not r.ok:
                        log(f"    POST failed: {r.status_code} {r.text[:300]}")
                        r.raise_for_status()
                created.append(vm["name"])

    # Stranded = NetBox VMs not in any PVE host's live output
    for nb_name, nb_vm in nb_vms.items():
        if nb_name not in seen_names:
            stranded.append(nb_name)
            log(f"  ? stranded (in NetBox but not live in PVE): {nb_name}")

    log(f"\nSummary: created={len(created)} updated={len(updated)} unchanged={len(unchanged)} stranded={len(stranded)}")
    if DRY_RUN:
        log("(dry-run — no NetBox writes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
