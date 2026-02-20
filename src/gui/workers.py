"""Background workers for audio compression tasks."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from ..backends.base import BaseAudioCodec

logger = logging.getLogger(__name__)


class CompressWorker(QThread):
    """Runs compression in a background thread."""

    progress = Signal(str, int, int)  # (message, current, total)
    finished_signal = Signal(object)  # CompressResult
    error = Signal(str)

    def __init__(
        self,
        codec: BaseAudioCodec,
        audio_path: Path,
        output_path: Path,
        params: dict,
        parent=None,
    ):
        super().__init__(parent)
        self._codec = codec
        self._audio_path = audio_path
        self._output_path = output_path
        self._params = params

    def run(self):
        try:
            result = self._codec.compress(
                self._audio_path,
                self._output_path,
                self._params,
                progress_cb=self._on_progress,
            )
            self.finished_signal.emit(result)
        except Exception as exc:
            logger.exception("Compression failed")
            self.error.emit(str(exc))

    def _on_progress(self, msg: str, current: int, total: int) -> None:
        self.progress.emit(msg, current, total)


class DecompressWorker(QThread):
    """Runs decompression in a background thread."""

    progress = Signal(str, int, int)
    finished_signal = Signal(object)  # DecompressResult
    error = Signal(str)

    def __init__(
        self,
        codec: BaseAudioCodec,
        compressed_path: Path,
        output_path: Path,
        parent=None,
    ):
        super().__init__(parent)
        self._codec = codec
        self._compressed_path = compressed_path
        self._output_path = output_path

    def run(self):
        try:
            result = self._codec.decompress(
                self._compressed_path,
                self._output_path,
                progress_cb=self._on_progress,
            )
            self.finished_signal.emit(result)
        except Exception as exc:
            logger.exception("Decompression failed")
            self.error.emit(str(exc))

    def _on_progress(self, msg: str, current: int, total: int) -> None:
        self.progress.emit(msg, current, total)


class BatchCompressWorker(QThread):
    """Compresses a list of audio files sequentially."""

    file_started = Signal(int, str)  # (index, filename)
    file_progress = Signal(int, str, int, int)  # (index, msg, current, total)
    file_finished = Signal(int, object)  # (index, CompressResult)
    file_error = Signal(int, str)  # (index, error_msg)
    all_done = Signal()

    def __init__(
        self,
        codec: BaseAudioCodec,
        audio_paths: list[Path],
        output_dir: Path,
        params: dict,
        parent=None,
    ):
        super().__init__(parent)
        self._codec = codec
        self._paths = audio_paths
        self._output_dir = output_dir
        self._params = params
        self._cancelled = False

    def run(self):
        for i, path in enumerate(self._paths):
            if self._cancelled:
                break
            self.file_started.emit(i, path.name)
            try:
                output = self._output_dir / path.stem

                def progress_cb(msg, current, total, idx=i):
                    self.file_progress.emit(idx, msg, current, total)

                result = self._codec.compress(
                    path, output, self._params, progress_cb=progress_cb
                )
                self.file_finished.emit(i, result)
            except Exception as exc:
                logger.exception("Batch compress failed for %s", path.name)
                self.file_error.emit(i, str(exc))

        self.all_done.emit()

    def cancel(self):
        self._cancelled = True
