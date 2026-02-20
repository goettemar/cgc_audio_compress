"""Backend registry — register, get and list codecs."""

from __future__ import annotations

from .backends.base import BaseAudioCodec

_codecs: dict[str, BaseAudioCodec] = {}


def register(codec: BaseAudioCodec) -> None:
    _codecs[codec.name] = codec


def get(name: str) -> BaseAudioCodec:
    return _codecs[name]


def list_codecs() -> list[BaseAudioCodec]:
    return list(_codecs.values())


def names() -> list[str]:
    return list(_codecs.keys())
