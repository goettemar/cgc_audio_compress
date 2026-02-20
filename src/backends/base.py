"""Abstract base class for audio compression backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable

from ..models import CompressResult, DecompressResult, ParamSpec

ProgressCallback = Callable[[str, int, int], None]


class BaseAudioCodec(ABC):
    """Interface every audio compression backend must implement."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    @abstractmethod
    def file_suffix(self) -> str: ...

    @abstractmethod
    def default_params(self) -> list[ParamSpec]: ...

    @abstractmethod
    def compress(
        self,
        audio_path: Path,
        output_path: Path,
        params: dict,
        progress_cb: ProgressCallback | None = None,
    ) -> CompressResult: ...

    @abstractmethod
    def decompress(
        self,
        compressed_path: Path,
        output_path: Path,
        progress_cb: ProgressCallback | None = None,
    ) -> DecompressResult: ...
