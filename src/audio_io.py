"""Audio I/O utilities wrapping torchaudio with ffmpeg fallback."""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path

import torch
import torchaudio

from .models import AudioInfo

logger = logging.getLogger(__name__)


def load_audio(path: str | Path) -> tuple[torch.Tensor, int]:
    """Load audio file and return (waveform, sample_rate).

    Waveform shape: (channels, samples).
    """
    path = Path(path)
    waveform, sr = torchaudio.load(str(path))
    return waveform, sr


def save_audio(waveform: torch.Tensor, path: str | Path, sample_rate: int) -> None:
    """Save waveform tensor to audio file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    torchaudio.save(str(path), waveform, sample_rate)


def get_audio_info(path: str | Path) -> AudioInfo:
    """Get audio file metadata via ffprobe (fast, no decoding)."""
    path = Path(path)
    try:
        return _get_info_ffprobe(path)
    except Exception:
        logger.debug("ffprobe failed, falling back to torchaudio.load", exc_info=True)
        return _get_info_load(path)


def _get_info_ffprobe(path: Path) -> AudioInfo:
    """Get metadata via ffprobe without decoding the file."""
    result = subprocess.run(
        [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            "-select_streams", "a:0",
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffprobe failed: {result.stderr}")

    probe = json.loads(result.stdout)

    stream = probe.get("streams", [{}])[0]
    fmt = probe.get("format", {})

    sample_rate = int(stream.get("sample_rate", 0))
    channels = int(stream.get("channels", 0))
    duration = float(fmt.get("duration", 0))
    bitrate_kbps = float(fmt.get("bit_rate", 0)) / 1000

    format_name = path.suffix.lstrip(".").upper() or "Unknown"

    return AudioInfo(
        duration=duration,
        channels=channels,
        sample_rate=sample_rate,
        bitrate_kbps=bitrate_kbps,
        format_name=format_name,
    )


def _get_info_load(path: Path) -> AudioInfo:
    """Fallback: get metadata by loading with torchaudio."""
    waveform, sr = torchaudio.load(str(path))
    channels = waveform.shape[0]
    duration = waveform.shape[1] / sr
    file_size = path.stat().st_size
    bitrate_kbps = (file_size * 8 / duration / 1000) if duration > 0 else 0.0
    format_name = path.suffix.lstrip(".").upper() or "Unknown"

    return AudioInfo(
        duration=duration,
        channels=channels,
        sample_rate=sr,
        bitrate_kbps=bitrate_kbps,
        format_name=format_name,
    )
