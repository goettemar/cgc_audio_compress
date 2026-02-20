# CGC Audio Compress

Neural Audio Compression mit Meta EnCodec. Teil der CGC-Tool-Familie.

## Architektur

- **Backend-System**: Registry + BaseAudioCodec ABC (Pattern aus cgc_image_compress)
- **EnCodec Backend**: 24kHz Mono + 48kHz Stereo, Bandbreiten 1.5–24 kbps
- **GUI**: PySide6 mit Tabs (Compress, Decompress, Batch, Settings)
- **Workers**: QThread-basiert, GPU wenn CUDA verfuegbar
- **Config**: JSON Persistence in data/config.json

## Konventionen

- Deutsche GUI-Labels, englischer Code
- Dataclass-basierte Models (ParamSpec, CompressResult etc.)
- Auto-Registration der Backends via __init__.py Import
- start.sh folgt CGC Launcher Pattern (venv + deps)
