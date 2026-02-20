"""Application state and configuration with JSON persistence."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent.parent / "data"
CONFIG_FILE = DATA_DIR / "config.json"


@dataclass
class AppConfig:
    default_backend: str = "EnCodec 48kHz"
    default_bandwidth: str = "6.0"
    output_dir: str = ""
    use_lm: bool = False
    last_audio_dir: str = ""

    def save(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_FILE.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")

    @classmethod
    def load(cls) -> AppConfig:
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                return cls(
                    **{k: v for k, v in data.items() if k in cls.__dataclass_fields__}
                )
            except Exception:
                logger.warning("Config load failed, using defaults", exc_info=True)
        return cls()


@dataclass
class AppState:
    config: AppConfig = field(default_factory=AppConfig)


_state: AppState | None = None


def get_state() -> AppState:
    """Singleton access to application state."""
    global _state
    if _state is None:
        _state = AppState(config=AppConfig.load())
    return _state
