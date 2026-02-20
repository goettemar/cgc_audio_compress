"""EnCodec backend — Meta's neural audio codec at 24kHz and 48kHz."""

from __future__ import annotations

import io
import logging
import time
from pathlib import Path

import torch
import torchaudio

from .. import registry
from ..audio_io import load_audio
from ..models import CompressResult, DecompressResult, ParamSpec, ParamType
from .base import BaseAudioCodec, ProgressCallback

logger = logging.getLogger(__name__)


def _get_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


class EnCodecBackend(BaseAudioCodec):
    """EnCodec compression backend."""

    def __init__(self, model_sr: int = 48000):
        self._model_sr = model_sr
        self._model = None

    @property
    def name(self) -> str:
        return f"EnCodec {self._model_sr // 1000}kHz"

    @property
    def description(self) -> str:
        return f"Meta EnCodec neural audio codec at {self._model_sr // 1000}kHz"

    @property
    def file_suffix(self) -> str:
        return ".ecdc"

    def default_params(self) -> list[ParamSpec]:
        if self._model_sr == 48000:
            bw_choices = ["3.0", "6.0", "12.0", "24.0"]
            bw_default = "6.0"
        else:
            bw_choices = ["1.5", "3.0", "6.0", "12.0", "24.0"]
            bw_default = "6.0"
        return [
            ParamSpec(
                name="bandwidth",
                label="Bitrate (kbps)",
                type=ParamType.CHOICE,
                default=bw_default,
                choices=bw_choices,
            ),
        ]

    def _load_model(self) -> None:
        if self._model is not None:
            return
        from encodec import EncodecModel

        if self._model_sr == 48000:
            self._model = EncodecModel.encodec_model_48khz()
        else:
            self._model = EncodecModel.encodec_model_24khz()
        self._model.to(_get_device())
        self._model.eval()

    def compress(
        self,
        audio_path: Path,
        output_path: Path,
        params: dict,
        progress_cb: ProgressCallback | None = None,
    ) -> CompressResult:
        if progress_cb:
            progress_cb("Lade Modell...", 0, 100)

        self._load_model()
        device = _get_device()
        bandwidth = float(params.get("bandwidth", 6.0))
        self._model.set_target_bandwidth(bandwidth)

        if progress_cb:
            progress_cb("Lade Audio...", 10, 100)

        # Load and prepare audio
        waveform, sr = load_audio(audio_path)
        original_size = audio_path.stat().st_size
        duration = waveform.shape[1] / sr

        # Resample if needed
        if sr != self._model_sr:
            if progress_cb:
                progress_cb(f"Resample {sr} -> {self._model_sr} Hz...", 20, 100)
            waveform = torchaudio.functional.resample(waveform, sr, self._model_sr)

        # Ensure correct channel count
        if self._model_sr == 48000:
            # 48kHz model expects stereo
            if waveform.shape[0] == 1:
                waveform = waveform.repeat(2, 1)
            elif waveform.shape[0] > 2:
                waveform = waveform[:2]
        else:
            # 24kHz model expects mono
            if waveform.shape[0] > 1:
                waveform = waveform.mean(dim=0, keepdim=True)

        # Add batch dimension: (1, channels, samples)
        audio = waveform.unsqueeze(0).to(device)

        if progress_cb:
            progress_cb("Komprimiere...", 30, 100)

        t0 = time.perf_counter()

        with torch.no_grad():
            encoded_frames = self._model.encode(audio)

        if progress_cb:
            progress_cb("Speichere...", 80, 100)

        # Serialize frames with torch.save
        out = Path(str(output_path).removesuffix(self.file_suffix) + self.file_suffix)
        out.parent.mkdir(parents=True, exist_ok=True)

        # Store codes + scales + metadata
        save_data = {
            "model_sr": self._model_sr,
            "bandwidth": bandwidth,
            "frames": [
                (codes.cpu(), scale.cpu() if scale is not None else None)
                for codes, scale in encoded_frames
            ],
        }
        buf = io.BytesIO()
        torch.save(save_data, buf)
        out.write_bytes(buf.getvalue())

        encode_time = time.perf_counter() - t0
        compressed_size = out.stat().st_size
        ratio = original_size / compressed_size if compressed_size > 0 else 0.0
        compressed_bitrate = (compressed_size * 8 / duration / 1000) if duration > 0 else 0.0
        original_bitrate = (original_size * 8 / duration / 1000) if duration > 0 else 0.0

        if progress_cb:
            progress_cb("Fertig", 100, 100)

        return CompressResult(
            source_path=audio_path,
            compressed_path=out,
            original_size=original_size,
            compressed_size=compressed_size,
            ratio=ratio,
            original_bitrate_kbps=original_bitrate,
            compressed_bitrate_kbps=compressed_bitrate,
            duration=duration,
            encode_time=encode_time,
            backend_name=self.name,
            params=params,
        )

    def decompress(
        self,
        compressed_path: Path,
        output_path: Path,
        progress_cb: ProgressCallback | None = None,
    ) -> DecompressResult:
        if progress_cb:
            progress_cb("Lade Modell...", 0, 100)

        self._load_model()
        device = _get_device()

        if progress_cb:
            progress_cb("Lade komprimierte Datei...", 20, 100)

        save_data = torch.load(compressed_path, map_location="cpu", weights_only=False)
        encoded_frames = save_data["frames"]

        if progress_cb:
            progress_cb("Dekomprimiere...", 40, 100)

        t0 = time.perf_counter()

        # Move frames to device
        encoded_frames = [
            (codes.to(device), scale.to(device) if scale is not None else None)
            for codes, scale in encoded_frames
        ]

        with torch.no_grad():
            audio = self._model.decode(encoded_frames)

        decode_time = time.perf_counter() - t0

        # audio shape: (1, channels, samples) — remove batch dim
        waveform = audio.squeeze(0).cpu()
        duration = waveform.shape[1] / self._model_sr

        if progress_cb:
            progress_cb("Speichere WAV...", 80, 100)

        wav_out = Path(str(output_path).removesuffix(".wav") + ".wav")
        wav_out.parent.mkdir(parents=True, exist_ok=True)
        torchaudio.save(str(wav_out), waveform, self._model_sr)

        if progress_cb:
            progress_cb("Fertig", 100, 100)

        return DecompressResult(
            compressed_path=compressed_path,
            output_path=wav_out,
            decode_time=decode_time,
            duration=duration,
        )


# Auto-register both variants
registry.register(EnCodecBackend(48000))
registry.register(EnCodecBackend(24000))
