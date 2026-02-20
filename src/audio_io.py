"""Audio I/O utilities wrapping torchaudio."""

from __future__ import annotations

from pathlib import Path

import torch
import torchaudio

from .models import AudioInfo


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
    """Get audio file metadata."""
    path = Path(path)
    info = torchaudio.info(str(path))
    duration = info.num_frames / info.sample_rate
    file_size = path.stat().st_size
    bitrate_kbps = (file_size * 8 / duration / 1000) if duration > 0 else 0.0

    # Determine format from suffix
    fmt = path.suffix.lstrip(".").upper()
    if fmt == "":
        fmt = "Unknown"

    return AudioInfo(
        duration=duration,
        channels=info.num_channels,
        sample_rate=info.sample_rate,
        bitrate_kbps=bitrate_kbps,
        format_name=fmt,
    )
