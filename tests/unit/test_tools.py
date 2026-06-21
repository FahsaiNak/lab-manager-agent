"""Unit tests for app/tools.py business logic — no LLM calls.

Covers SPEC.md §5 Storage Steward eval cases 1-2 (staleness), 3 (anomaly
detection), 5's non-LLM half (propose never touches the filesystem), plus
the Slack dedup/rate-limit logic underlying eval case 4.
"""

import json
import os
import time

from app import tools


def _touch(path, age_days, owner=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("data")
    mtime = time.time() - age_days * 86400
    os.utime(path, (mtime, mtime))
    if owner:
        with open(str(path) + ".owner", "w") as f:
            f.write(owner)


def test_scan_filesystem_flags_stale_dirs(tmp_path):
    _touch(tmp_path / "proj/userA/old/file.txt", age_days=120, owner="userA")
    _touch(tmp_path / "proj/userA/recent/file.txt", age_days=10, owner="userA")

    result = tools.scan_filesystem(str(tmp_path))
    stale = [e for e in result["entries"] if e["is_stale"]]
    fresh = [e for e in result["entries"] if not e["is_stale"]]

    assert len(stale) == 1
    assert len(fresh) == 1
    assert stale[0]["owner"] == "userA"


def test_find_unauthorized_writes_detects_anomaly(tmp_path, monkeypatch):
    _touch(tmp_path / "proj/owner_user/file.txt", age_days=1, owner="owner_user")
    _touch(tmp_path / "proj/intruder/file.txt", age_days=1, owner="intruder")

    groups_path = tmp_path / "authorized_groups.json"
    groups_path.write_text(json.dumps({"proj": ["owner_user"]}))
    monkeypatch.setattr(tools, "AUTHORIZED_GROUPS_PATH", str(groups_path))

    result = tools.find_unauthorized_writes(str(tmp_path))
    anomalies = result["anomalies"]

    assert len(anomalies) == 1
    assert anomalies[0]["owner"] == "intruder"


def test_find_unauthorized_writes_no_anomaly_for_authorized_user(tmp_path, monkeypatch):
    _touch(tmp_path / "proj/owner_user/file.txt", age_days=1, owner="owner_user")

    groups_path = tmp_path / "authorized_groups.json"
    groups_path.write_text(json.dumps({"proj": ["owner_user"]}))
    monkeypatch.setattr(tools, "AUTHORIZED_GROUPS_PATH", str(groups_path))

    result = tools.find_unauthorized_writes(str(tmp_path))
    assert result["anomalies"] == []


def test_propose_archive_plan_does_not_touch_filesystem(tmp_path):
    target = tmp_path / "stale_file.txt"
    target.write_text("data")

    result = tools.propose_archive_plan([str(target)])

    assert result["status"] == "proposed"
    assert target.exists()


def test_post_to_slack_dedups_repeated_alert(tmp_path, monkeypatch):
    log_path = tmp_path / "slack_mock_log.json"
    monkeypatch.setattr(tools, "SLACK_LOG_PATH", str(log_path))

    first = tools.post_to_slack("#alerts", "anomaly found", dedup_key="path/a")
    second = tools.post_to_slack("#alerts", "anomaly found again", dedup_key="path/a")

    assert first["status"] == "posted"
    assert second["status"] == "skipped_duplicate"


def test_post_to_slack_rate_limits_within_window(tmp_path, monkeypatch):
    log_path = tmp_path / "slack_mock_log.json"
    monkeypatch.setattr(tools, "SLACK_LOG_PATH", str(log_path))
    monkeypatch.setattr(tools, "MAX_SLACK_POSTS_PER_WINDOW", 2)

    tools.post_to_slack("#alerts", "msg1", dedup_key="k1")
    tools.post_to_slack("#alerts", "msg2", dedup_key="k2")
    third = tools.post_to_slack("#alerts", "msg3", dedup_key="k3")

    assert third["status"] == "rate_limited"
