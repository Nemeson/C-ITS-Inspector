from __future__ import annotations

from pathlib import Path

from pcap2kml_player.app_memory import AppMemory


def test_app_memory_roundtrip(tmp_path: Path, monkeypatch) -> None:
    storage_file = tmp_path / "memory.json"
    monkeypatch.setattr(AppMemory, "storage_path", classmethod(lambda cls: storage_file))

    first = tmp_path / "capture-1.pcap"
    second = tmp_path / "capture-2.pcap"
    first.write_text("x", encoding="utf-8")
    second.write_text("y", encoding="utf-8")

    memory = AppMemory()
    memory.remember_files([str(first), str(second)])
    memory.remember_export_directory(str(tmp_path / "export"))
    memory.remember_session_summary(
        message_count=15,
        station_count=2,
        duration_seconds=42.5,
        msg_type_counts={"CAM": 10, "SPATEM": 5},
    )
    memory.save()

    loaded = AppMemory.load()

    assert loaded.last_opened_files == [str(first.resolve()), str(second.resolve())]
    assert loaded.last_directory == str(first.resolve().parent)
    assert loaded.last_export_directory == str((tmp_path / "export").resolve())
    assert loaded.last_session_message_count == 15
    assert loaded.last_session_types == {"CAM": 10, "SPATEM": 5}


def test_existing_last_session_files_filters_missing_entries(tmp_path: Path, monkeypatch) -> None:
    storage_file = tmp_path / "memory.json"
    monkeypatch.setattr(AppMemory, "storage_path", classmethod(lambda cls: storage_file))

    existing = tmp_path / "existing.pcap"
    existing.write_text("ok", encoding="utf-8")
    missing = tmp_path / "missing.pcap"

    memory = AppMemory(last_opened_files=[str(existing), str(missing)])

    assert memory.existing_last_session_files() == [str(existing)]
