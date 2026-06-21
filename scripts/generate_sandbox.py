"""
Generates sandbox/cluster_fs/, the synthetic HPC-cluster-style filesystem used to
demo the Storage Steward sub-agent.

Git does not preserve file mtimes on clone, so "this directory is 120 days stale"
can't be checked into the repo as static files — it has to be regenerated here,
each run, relative to the current time. Run this before any Storage Steward demo/eval.

Builds exactly the fixtures referenced in SPEC.md eval cases 1-3:
  1. plm-epistasis/fahsai/run_old      -> mtime 120 days ago (archive candidate)
  2. plm-epistasis/fahsai/run_recent   -> mtime 10 days ago (NOT an archive candidate)
  3. combatrl/guest_user/sneaky_upload -> written by a user not in combatrl's
     authorized_groups.json list (anomaly candidate)
"""

import json
import os
import time

SANDBOX_ROOT = os.path.join(os.path.dirname(__file__), "..", "sandbox")
CLUSTER_FS_ROOT = os.path.join(SANDBOX_ROOT, "cluster_fs")
AUTHORIZED_GROUPS_PATH = os.path.join(SANDBOX_ROOT, "authorized_groups.json")

DAY = 86400


def _write_file(path: str, content: str, owner: str, age_days: float) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    mtime = time.time() - age_days * DAY
    os.utime(path, (mtime, mtime))
    # Synthetic "owner" metadata stored alongside, since real OS file ownership
    # can't be faked without root. The Storage Steward reads this sidecar file
    # instead of POSIX uid/gid.
    with open(path + ".owner", "w") as f:
        f.write(owner)


def main() -> None:
    with open(AUTHORIZED_GROUPS_PATH) as f:
        authorized_groups = json.load(f)

    fixtures = [
        # (relative path, content, owner, age_days)
        ("plm-epistasis/fahsai/run_old/results.csv",
         "epoch,loss\n1,0.91\n2,0.84\n", "fahsai", 120),
        ("plm-epistasis/fahsai/run_recent/results.csv",
         "epoch,loss\n1,0.55\n2,0.41\n", "fahsai", 10),
        ("combatrl/fahsai/checkpoint_old/model.bin",
         "synthetic checkpoint bytes", "fahsai", 150),
        # Anomaly fixture: guest_user is not in authorized_groups["combatrl"]
        ("combatrl/guest_user/sneaky_upload/data.bin",
         "synthetic unauthorized upload", "guest_user", 1),
    ]

    for rel_path, content, owner, age_days in fixtures:
        _write_file(os.path.join(CLUSTER_FS_ROOT, rel_path), content, owner, age_days)

    print(f"Sandbox cluster filesystem written to {CLUSTER_FS_ROOT}")
    print(f"Authorized groups loaded from {AUTHORIZED_GROUPS_PATH}: {authorized_groups}")


if __name__ == "__main__":
    main()
