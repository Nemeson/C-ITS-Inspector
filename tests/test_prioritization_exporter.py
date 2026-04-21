"""Tests for prioritization issue CSV/JSON export."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone

from pcap2kml_player.data_model import CaptureRole, MessageSource, MessageType, V2xMessage
from pcap2kml_player.prioritization_exporter import export_prioritization_issues


def test_export_prioritization_issues_writes_csv_and_json(tmp_path):
    now = datetime(2026, 4, 18, 12, 0, 0, tzinfo=timezone.utc)
    messages = [
        V2xMessage(
            timestamp=now,
            station_id="bus-1",
            msg_type=MessageType.SREM,
            latitude=52.0,
            longitude=13.0,
            source=MessageSource(
                path="C:/captures/rsu_txa.pcap",
                filename="rsu_txa.pcap",
                source_index=0,
                role=CaptureRole.TXA,
            ),
            merge_group_id="merge-00001",
            merge_confidence=0.91,
            decoded_data={
                "intersectionId": 42,
                "requestId": 12,
                "sequenceNumber": 1,
                "inLane": 1,
                "outLane": 3,
            },
        ),
        V2xMessage(
            timestamp=now + timedelta(seconds=2),
            station_id="bus-1",
            msg_type=MessageType.CAM,
            latitude=52.0,
            longitude=13.0,
        ),
    ]

    created = export_prioritization_issues(messages, tmp_path)

    assert {path.name for path in created} == {
        "prioritization_issues.csv",
        "prioritization_issues.json",
        "prioritization_report.json",
    }
    with (tmp_path / "prioritization_issues.csv").open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    with (tmp_path / "prioritization_issues.json").open(encoding="utf-8") as handle:
        json_rows = json.load(handle)

    assert rows[0]["issue_type"] == "TIMEOUT"
    assert rows[0]["intersection_id"] == "42"
    assert rows[0]["source_roles"] == "TXA"
    assert rows[0]["source_files"] == "rsu_txa.pcap"
    assert rows[0]["merge_group_id"] == "merge-00001"
    assert json_rows[0]["issue_type"] == "TIMEOUT"

    with (tmp_path / "prioritization_report.json").open(encoding="utf-8") as handle:
        report = json.load(handle)
    assert report["total_issues"] == 1
    assert report["issues_by_type"]["TIMEOUT"] == 1
    assert report["source_roles"]["TXA"] == 1
