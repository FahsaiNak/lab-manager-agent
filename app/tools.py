"""Custom tools for the Lab Manager sub-agents.

Tool contracts follow SPEC.md §3. All filesystem tools operate against the
sandboxed synthetic cluster in sandbox/cluster_fs/ (see scripts/generate_sandbox.py) —
never a real lab filesystem.
"""

import json
import os
import time

_APP_DIR = os.path.dirname(__file__)
_PROJECT_ROOT = os.path.join(_APP_DIR, "..")
SANDBOX_ROOT = os.path.join(_PROJECT_ROOT, "sandbox")
CLUSTER_FS_ROOT = os.path.abspath(os.path.join(SANDBOX_ROOT, "cluster_fs"))
AUTHORIZED_GROUPS_PATH = os.path.join(SANDBOX_ROOT, "authorized_groups.json")
SLACK_LOG_PATH = os.path.abspath(os.path.join(_PROJECT_ROOT, "slack_mock_log.json"))

STALE_THRESHOLD_DAYS = 90
MAX_SLACK_POSTS_PER_WINDOW = 5
SLACK_RATE_WINDOW_SECONDS = 60


def scan_filesystem(root_path: str) -> dict:
    """Scans a directory tree and reports metadata for every file found.

    Args:
        root_path: Absolute path to the directory tree to scan.

    Returns:
        dict with 'status' and 'entries'. Each entry has path, project (the
        top-level directory under root_path), owner, age_days, and is_stale
        (age_days greater than 90).
    """
    entries = []
    now = time.time()
    for dirpath, _dirnames, filenames in os.walk(root_path):
        for fname in filenames:
            if fname.endswith(".owner"):
                continue
            fpath = os.path.join(dirpath, fname)
            owner_path = fpath + ".owner"
            owner = "unknown"
            if os.path.exists(owner_path):
                with open(owner_path) as f:
                    owner = f.read().strip()
            rel = os.path.relpath(fpath, root_path)
            project = rel.split(os.sep)[0]
            age_days = (now - os.path.getmtime(fpath)) / 86400
            entries.append(
                {
                    "path": fpath,
                    "project": project,
                    "owner": owner,
                    "age_days": round(age_days, 1),
                    "is_stale": age_days > STALE_THRESHOLD_DAYS,
                }
            )
    return {"status": "success", "entries": entries}


def find_unauthorized_writes(root_path: str) -> dict:
    """Cross-references file ownership against each project's authorized user list.

    Args:
        root_path: Absolute path to the directory tree to scan.

    Returns:
        dict with 'status' and 'anomalies' — file entries whose owner is not
        in the authorized list for that project, per authorized_groups.json.
    """
    scan = scan_filesystem(root_path)
    with open(AUTHORIZED_GROUPS_PATH) as f:
        authorized_groups = json.load(f)

    anomalies = []
    for entry in scan["entries"]:
        allowed = authorized_groups.get(entry["project"])
        if allowed is not None and entry["owner"] not in allowed:
            anomalies.append(entry)
    return {"status": "success", "anomalies": anomalies}


def propose_archive_plan(paths: list[str]) -> dict:
    """Builds an archive proposal for a list of file paths. Does not move or delete anything.

    Args:
        paths: Absolute file paths recommended for archival.

    Returns:
        dict with 'status', a generated 'plan_id', and the 'paths' included.
        Acting on the plan requires a separate, confirmed execute_archive_plan call.
    """
    plan_id = f"plan-{int(time.time())}"
    return {"status": "proposed", "plan_id": plan_id, "paths": paths}


def execute_archive_plan(plan_id: str, confirm: bool) -> dict:
    """Executes a previously proposed archive plan. Destructive — gated by guardrail.

    Args:
        plan_id: The plan identifier returned by propose_archive_plan.
        confirm: Must be True for this call to take effect.

    Returns:
        dict with 'status'. The agent's before_tool_callback guardrail blocks
        this call before it reaches this function unless confirm is True.
    """
    return {"status": "archived", "plan_id": plan_id}


def post_to_slack(channel: str, message: str, dedup_key: str) -> dict:
    """Posts a message to the lab's Slack channel (sandboxed/mock for this demo).

    Args:
        channel: Slack channel name, e.g. "#lab-storage-alerts".
        message: The message text to post.
        dedup_key: A stable key identifying what this alert is about (e.g. a
            file path) — used to suppress duplicate alerts across runs.

    Returns:
        dict with 'status' of 'posted', 'skipped_duplicate', or 'rate_limited'.
    """
    log = {"posts": [], "dedup_keys": []}
    if os.path.exists(SLACK_LOG_PATH):
        with open(SLACK_LOG_PATH) as f:
            log = json.load(f)

    if dedup_key in log["dedup_keys"]:
        return {"status": "skipped_duplicate", "dedup_key": dedup_key}

    now = time.time()
    recent_posts = [
        p for p in log["posts"] if now - p["ts"] < SLACK_RATE_WINDOW_SECONDS
    ]
    if len(recent_posts) >= MAX_SLACK_POSTS_PER_WINDOW:
        return {"status": "rate_limited", "dedup_key": dedup_key}

    log["posts"].append(
        {"channel": channel, "message": message, "dedup_key": dedup_key, "ts": now}
    )
    log["dedup_keys"].append(dedup_key)
    with open(SLACK_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)

    return {"status": "posted", "channel": channel, "message": message}
