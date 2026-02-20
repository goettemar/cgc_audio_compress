"""Decompression tab — .ecdc to WAV."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ... import registry
from ..state import get_state
from ..workers import DecompressWorker

ECDC_FILTER = "EnCodec (*.ecdc);;Alle Dateien (*)"


class DecompressTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: DecompressWorker | None = None
        self._compressed_path: Path | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # --- Source ---
        src_group = QGroupBox("Komprimierte Datei")
        src_layout = QHBoxLayout(src_group)
        self._path_edit = QLineEdit()
        self._path_edit.setReadOnly(True)
        self._path_edit.setPlaceholderText(".ecdc Datei waehlen...")
        src_layout.addWidget(self._path_edit)
        browse_btn = QPushButton("Durchsuchen")
        browse_btn.clicked.connect(self._browse)
        src_layout.addWidget(browse_btn)
        layout.addWidget(src_group)

        # --- Backend selector ---
        backend_group = QGroupBox("Backend")
        backend_layout = QHBoxLayout(backend_group)
        backend_layout.addWidget(QLabel("Backend:"))
        self._backend_combo = QComboBox()
        for codec in registry.list_codecs():
            self._backend_combo.addItem(codec.name)
        state = get_state()
        idx = self._backend_combo.findText(state.config.default_backend)
        if idx >= 0:
            self._backend_combo.setCurrentIndex(idx)
        backend_layout.addWidget(self._backend_combo, 1)
        layout.addWidget(backend_group)

        # --- Output ---
        out_group = QGroupBox("Ausgabe")
        out_layout = QHBoxLayout(out_group)
        self._output_edit = QLineEdit()
        self._output_edit.setPlaceholderText("Automatisch (neben Quelldatei)")
        out_layout.addWidget(self._output_edit)
        out_browse = QPushButton("Waehlen")
        out_browse.setProperty("class", "secondary")
        out_browse.clicked.connect(self._browse_output)
        out_layout.addWidget(out_browse)
        layout.addWidget(out_group)

        # --- Decompress ---
        self._decompress_btn = QPushButton("Dekomprimieren")
        self._decompress_btn.clicked.connect(self._start_decompress)
        self._decompress_btn.setEnabled(False)
        layout.addWidget(self._decompress_btn)

        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

        # --- Result ---
        self._result_group = QGroupBox("Ergebnis")
        result_layout = QVBoxLayout(self._result_group)
        self._result_label = QLabel()
        self._result_label.setWordWrap(True)
        result_layout.addWidget(self._result_label)
        self._result_group.setVisible(False)
        layout.addWidget(self._result_group)

        layout.addStretch()

    def _browse(self):
        state = get_state()
        start_dir = state.config.last_audio_dir or ""
        path, _ = QFileDialog.getOpenFileName(self, "Komprimierte Datei waehlen", start_dir, ECDC_FILTER)
        if not path:
            return
        self._compressed_path = Path(path)
        self._path_edit.setText(path)
        state.config.last_audio_dir = str(self._compressed_path.parent)
        state.config.save()
        self._decompress_btn.setEnabled(True)

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "Ausgabeverzeichnis waehlen")
        if path:
            self._output_edit.setText(path)

    def _start_decompress(self):
        if not self._compressed_path:
            return

        codec = registry.get(self._backend_combo.currentText())

        out_dir = self._output_edit.text().strip()
        if out_dir:
            output = Path(out_dir) / self._compressed_path.stem
        else:
            output = self._compressed_path.parent / self._compressed_path.stem

        self._decompress_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._progress.setValue(0)
        self._result_group.setVisible(False)
        self._status_label.setText("Dekomprimiere...")

        self._worker = DecompressWorker(codec, self._compressed_path, output, self)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_signal.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, msg: str, current: int, total: int):
        self._progress.setMaximum(total)
        self._progress.setValue(current)
        self._status_label.setText(msg)

    def _on_finished(self, result):
        self._decompress_btn.setEnabled(True)
        self._progress.setVisible(False)
        self._status_label.setText("Fertig!")

        self._result_label.setText(
            f"Dauer: {result.duration:.1f}s\n"
            f"Decode-Zeit: {result.decode_time:.2f}s\n"
            f"Ausgabe: {result.output_path}"
        )
        self._result_group.setVisible(True)
        self._worker = None

    def _on_error(self, msg: str):
        self._decompress_btn.setEnabled(True)
        self._progress.setVisible(False)
        self._status_label.setText(f"Fehler: {msg}")
        self._worker = None
