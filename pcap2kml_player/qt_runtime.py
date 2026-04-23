"""Qt/QtWebEngine runtime setup for Windows compatibility."""

from __future__ import annotations

import os


DEFAULT_CHROMIUM_FLAGS = (
    "--disable-direct-composition",
    "--disable-features=DirectComposition,DirectCompositionVideoOverlays,UseHDRTransferFunction",
    "--disable-accelerated-video-decode",
    "--disable-gpu-memory-buffer-video-frames",
    "--force-color-profile=srgb",
)
SOFTWARE_RENDERING_FLAGS = (
    "--disable-gpu",
    "--disable-gpu-compositing",
)


def configure_qt_runtime_environment() -> None:
    """Configure QtWebEngine before any PyQt imports happen.

    Some Windows machines emit Chromium/QtWebEngine D3D11/HDR errors such as
    QueryVideoProcessorCustomExtForHDR or show a gray WebEngine surface. The
    default favors stability and forces software rendering for the embedded map.

    Set PCAP2KML_ENABLE_GPU=1 to opt back into GPU rendering for testing on
    machines where QtWebEngine is known to be stable.
    """
    flags = list(DEFAULT_CHROMIUM_FLAGS)
    enable_gpu = os.environ.get("PCAP2KML_ENABLE_GPU", "").strip().lower() in {"1", "true", "yes"}
    disable_gpu = os.environ.get("PCAP2KML_DISABLE_GPU", "").strip().lower() in {"1", "true", "yes"}
    if disable_gpu or not enable_gpu:
        flags.extend(SOFTWARE_RENDERING_FLAGS)
        os.environ.setdefault("QT_OPENGL", "software")
        os.environ.setdefault("QT_QUICK_BACKEND", "software")

    _append_env_flags("QTWEBENGINE_CHROMIUM_FLAGS", flags)
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")


def _append_env_flags(env_name: str, flags: list[str]) -> None:
    """Append flags to an environment variable without duplicating entries."""
    existing = os.environ.get(env_name, "").split()
    merged = list(existing)
    for flag in flags:
        if flag not in merged:
            merged.append(flag)
    os.environ[env_name] = " ".join(merged).strip()
