# CGC Audio Compress

Neural Audio Compression mit Meta EnCodec. Teil der CGC-Tool-Familie.

## Architektur

- **Backend-System**: Registry + BaseAudioCodec ABC (Pattern aus cgc_image_compress)
- **EnCodec Backend**: 24kHz Mono + 48kHz Stereo, Bandbreiten 1.5–24 kbps
- **GUI**: PySide6 mit Tabs (Compress, Decompress, Batch, Settings)
- **Workers**: QThread-basiert, GPU wenn CUDA verfuegbar
- **Config**: JSON Persistence in data/config.json

## .ecdc Binaerformat

Kompaktes Format fuer EnCodec-Frames (shared mit cgc_video_compressor):

```
Header: ECDC<version:u8><model_sr:u32><bandwidth:f32><n_frames:u16>
Frame:  <has_scale:u8>[<scale:f32>]<n_codebooks:u16><n_steps:u32><codes:int16[]>
```

Legacy-Support: Alte Dateien mit anderem Header werden automatisch erkannt und geladen.

## Audio I/O

- `load_audio()`: torchaudio mit ffmpeg-Pipe-Fallback fuer MP3
- `get_audio_info()`: ffprobe (schnell, kein Decoding), Fallback torchaudio.load
- Abhaengigkeit `torchcodec` fuer torchaudio >=2.10

## Konventionen

- Deutsche GUI-Labels, englischer Code
- Dataclass-basierte Models (ParamSpec, CompressResult etc.)
- Auto-Registration der Backends via __init__.py Import
- start.sh folgt CGC Launcher Pattern (venv + deps)
- Metriken: SNR (dB) und Spectral Convergence via torch STFT
