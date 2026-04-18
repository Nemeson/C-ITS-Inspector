"""Persistent application memory for PCAP2KML Player."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from PyQt6.QtCore import QStandardPaths

MAX_RECENT_FILES = 10


@dataclass
class AppMemory:
    """Small persistent memory for recent files and the last session summary."""

    recent_files: list[str] = field(default_factory=list)
    last_opened_files: list[str] = field(default_factory=list)
    last_directory: str = ""
    last_export_directory: str = ""
    last_session_message_count: int = 0
    last_session_station_count: int = 0
    last_session_duration_seconds: float = 0.0
    last_session_types: dict[str, int] = field(default_factory=dict)

    @classmethod
    def storage_path(cls) -> Path:
        """Return the JSON file path used for persistent memory."""
        base_dir = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppDataLocation
        )
        if not base_dir:
            base_dir = str(Path.home() / ".pcap2kml_player")
        return Path(base_dir) / "memory.json"

    @classmethod
    def load(cls) -> "AppMemory":
        """Load persisted memory from disk if available."""
        path = cls.storage_path()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return cls()

        return cls(
            recent_files=list(data.get("recent_files", [])),
            last_opened_files=list(data.get("last_opened_files", [])),
            last_directory=str(data.get("last_directory", "")),
            last_export_directory=str(data.get("last_export_directory", "")),
            last_session_message_count=int(data.get("last_session_message_count", 0)),
            last_session_station_count=int(data.get("last_session_station_count", 0)),
            last_session_duration_seconds=float(
                data.get("last_session_duration_seconds", 0.0)
            ),
            last_session_types={
                str(key): int(value)
                for key, value in data.get("last_session_types", {}).items()
            },
        )

    def save(self) -> None:
        """Persist memory to disk."""
        path = self.storage_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(asdict(self), indent=2, ensure_ascii=True),
            encoding="utf-8",
        )

    def remember_files(self, paths: list[str]) -> None:
        """Store recent and last-opened files."""
        normalized = [str(Path(path).resolve()) for path in paths]
        if not normalized:
            return

        self.last_opened_files = normalized
        self.last_directory = str(Path(normalized[0]).parent)

        combined = normalized + self.recent_files
        seen: set[str] = set()
        deduped: list[str] = []
        for path in combined:
            if path in seen:
                continue
            seen.add(path)
            deduped.append(path)
        self.recent_files = deduped[:MAX_RECENT_FILES]

    def remember_export_directory(self, directory: str) -> None:
        """Store the last export target directory."""
        self.last_export_directory = str(Path(directory).resolve())

    def remember_session_summary(
        self,
        message_count: int,
        station_count: int,
        duration_seconds: float,
        msg_type_counts: dict[str, int],
    ) -> None:
        """Persist a compact summary of the last successful load."""
        self.last_session_message_count = message_count
        self.last_session_station_count = station_count
        self.last_session_duration_seconds = duration_seconds
        self.last_session_types = dict(sorted(msg_type_counts.items()))

    def existing_last_session_files(self) -> list[str]:
        """Return only the last-opened files that still exist."""
        return [path for path in self.last_opened_files if Path(path).exists()]

