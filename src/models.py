"""Data models for audio compression."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ParamType(Enum):
    INT = "int"
    FLOAT = "float"
    CHOICE = "choice"
    BOOL = "bool"


@dataclass
class ParamSpec:
    name: str
    label: str
    type: ParamType
    default: int | float | str | bool
    min: float | None = None
    max: float | None = None
    step: float | None = None
    choices: list[str] = field(default_factory=list)


@dataclass
class AudioInfo:
    duration: float
    channels: int
    sample_rate: int
    bitrate_kbps: float
    format_name: str


@dataclass
class CompressResult:
    source_path: Path
    compressed_path: Path
    original_size: int
    compressed_size: int
    ratio: float
    original_bitrate_kbps: float
    compressed_bitrate_kbps: float
    duration: float
    encode_time: float
    backend_name: str
    params: dict = field(default_factory=dict)


@dataclass
class DecompressResult:
    compressed_path: Path
    output_path: Path
    decode_time: float
    duration: float
