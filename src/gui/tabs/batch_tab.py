"""Batch audio compression tab."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ... import registry
from ...models import ParamType
from ..state import get_state
from ..workers import BatchCompressWorker

AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac"}


class BatchTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: BatchCompressWorker | None = None
        self._audio_paths: list[Path] = []
        self._results: list = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # --- Source ---
        src_group = QGroupBox("Quelldateien")
        src_layout = QVBoxLayout(src_group)

        btn_row = QHBoxLayout()
        self._folder_btn = QPushButton("Ordner waehlen")
        self._folder_btn.clicked.connect(self._browse_folder)
        btn_row.addWidget(self._folder_btn)
        self._files_btn = QPushButton("Dateien waehlen")
        self._files_btn.clicked.connect(self._browse_files)
        btn_row.addWidget(self._files_btn)
        self._clear_btn = QPushButton("Leeren")
        self._clear_btn.setProperty("class", "secondary")
        self._clear_btn.clicked.connect(self._clear_files)
        btn_row.addWidget(self._clear_btn)
        btn_row.addStretch()
        src_layout.addLayout(btn_row)

        self._file_count_label = QLabel("Keine Dateien ausgewaehlt")
        src_layout.addWidget(self._file_count_label)

        layout.addWidget(src_group)

        # --- Backend / params ---
        params_group = QGroupBox("Kompression")
        params_layout = QVBoxLayout(params_group)

        row = QHBoxLayout()
        row.addWidget(QLabel("Backend:"))
        self._backend_combo = QComboBox()
        for codec in registry.list_codecs():
            self._backend_combo.addItem(codec.name)
        state = get_state()
        idx = self._backend_combo.findText(state.config.default_backend)
        if idx >= 0:
            self._backend_combo.setCurrentIndex(idx)
        row.addWidget(self._backend_combo, 1)
        params_layout.addLayout(row)

        # Bandwidth selector
        bw_row = QHBoxLayout()
        bw_row.addWidget(QLabel("Bitrate (kbps):"))
        self._bw_combo = QComboBox()
        self._update_bw_choices()
        self._backend_combo.currentTextChanged.connect(lambda _: self._update_bw_choices())
        bw_row.addWidget(self._bw_combo, 1)
        params_layout.addLayout(bw_row)

        layout.addWidget(params_group)

        # --- Output ---
        out_group = QGroupBox("Ausgabeverzeichnis")
        out_layout = QHBoxLayout(out_group)
        self._output_edit = QLineEdit()
        self._output_edit.setPlaceholderText("Pflichtfeld — Ausgabeverzeichnis waehlen")
        out_layout.addWidget(self._output_edit)
        out_browse = QPushButton("Waehlen")
        out_browse.setProperty("class", "secondary")
        out_browse.clicked.connect(self._browse_output)
        out_layout.addWidget(out_browse)
        layout.addWidget(out_group)

        # --- Start / Cancel ---
        action_row = QHBoxLayout()
        self._start_btn = QPushButton("Batch starten")
        self._start_btn.clicked.connect(self._start_batch)
        self._start_btn.setEnabled(False)
        action_row.addWidget(self._start_btn)
        self._cancel_btn = QPushButton("Abbrechen")
        self._cancel_btn.setProperty("class", "secondary")
        self._cancel_btn.clicked.connect(self._cancel_batch)
        self._cancel_btn.setEnabled(False)
        action_row.addWidget(self._cancel_btn)
        layout.addLayout(action_row)

        self._progress = QProgressBar()
        self._progress.setVisible(False)
        layout.addWidget(self._progress)

        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

        # --- Results table ---
        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels(["Datei", "Original", "Komprimiert", "Ratio", "Status"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.setVisible(False)
        layout.addWidget(self._table)

        # --- Summary ---
        self._summary_group = QGroupBox("Zusammenfassung")
        summary_layout = QVBoxLayout(self._summary_group)
        self._summary_label = QLabel()
        self._summary_label.setWordWrap(True)
        summary_layout.addWidget(self._summary_label)
        self._summary_group.setVisible(False)
        layout.addWidget(self._summary_group)

    def _update_bw_choices(self):
        self._bw_combo.clear()
        codec = registry.get(self._backend_combo.currentText())
        for spec in codec.default_params():
            if spec.name == "bandwidth":
                self._bw_combo.addItems(spec.choices)
                state = get_state()
                idx = self._bw_combo.findText(state.config.default_bandwidth)
                if idx >= 0:
                    self._bw_combo.setCurrentIndex(idx)
                break

    def _browse_folder(self):
        state = get_state()
        path = QFileDialog.getExistingDirectory(
            self, "Ordner waehlen", state.config.last_audio_dir or ""
        )
        if not path:
            return
        folder = Path(path)
        state.config.last_audio_dir = str(folder)
        state.config.save()
        self._audio_paths = sorted(
            f for f in folder.iterdir() if f.suffix.lower() in AUDIO_EXTENSIONS
        )
        self._update_file_count()

    def _browse_files(self):
        state = get_state()
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Audio-Dateien waehlen",
            state.config.last_audio_dir or "",
            "Audio (*.wav *.mp3 *.flac *.ogg *.m4a *.aac);;Alle Dateien (*)",
        )
        if not files:
            return
        self._audio_paths = [Path(f) for f in files]
        if self._audio_paths:
            state.config.last_audio_dir = str(self._audio_paths[0].parent)
            state.config.save()
        self._update_file_count()

    def _clear_files(self):
        self._audio_paths = []
        self._update_file_count()

    def _update_file_count(self):
        n = len(self._audio_paths)
        self._file_count_label.setText(
            f"{n} Datei(en) ausgewaehlt" if n > 0 else "Keine Dateien ausgewaehlt"
        )
        self._start_btn.setEnabled(n > 0)

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "Ausgabeverzeichnis waehlen")
        if path:
            self._output_edit.setText(path)

    def _start_batch(self):
        out_dir = self._output_edit.text().strip()
        if not out_dir:
            self._status_label.setText("Bitte Ausgabeverzeichnis waehlen!")
            return
        if not self._audio_paths:
            return

        output_dir = Path(out_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        codec = registry.get(self._backend_combo.currentText())
        params = {"bandwidth": self._bw_combo.currentText()}

        self._results = []
        self._table.setRowCount(len(self._audio_paths))
        self._table.setVisible(True)
        self._summary_group.setVisible(False)
        for i, p in enumerate(self._audio_paths):
            self._table.setItem(i, 0, QTableWidgetItem(p.name))
            for col in range(1, 5):
                self._table.setItem(i, col, QTableWidgetItem(""))
            self._table.setItem(i, 4, QTableWidgetItem("Wartend"))

        self._start_btn.setEnabled(False)
        self._cancel_btn.setEnabled(True)
        self._progress.setVisible(True)
        self._progress.setMaximum(len(self._audio_paths))
        self._progress.setValue(0)

        self._worker = BatchCompressWorker(codec, self._audio_paths, output_dir, params, self)
        self._worker.file_started.connect(self._on_file_started)
        self._worker.file_finished.connect(self._on_file_finished)
        self._worker.file_error.connect(self._on_file_error)
        self._worker.all_done.connect(self._on_all_done)
        self._worker.start()

    def _cancel_batch(self):
        if self._worker:
            self._worker.cancel()
            self._status_label.setText("Abbruch angefordert...")

    def _on_file_started(self, idx: int, filename: str):
        self._table.setItem(idx, 4, QTableWidgetItem("Komprimiere..."))
        self._status_label.setText(f"[{idx + 1}/{len(self._audio_paths)}] {filename}")

    def _on_file_finished(self, idx: int, result):
        self._results.append(result)
        self._table.setItem(idx, 1, QTableWidgetItem(f"{result.original_size / 1024:.1f} KB"))
        self._table.setItem(idx, 2, QTableWidgetItem(f"{result.compressed_size / 1024:.1f} KB"))
        self._table.setItem(idx, 3, QTableWidgetItem(f"{result.ratio:.1f}x"))
        self._table.setItem(idx, 4, QTableWidgetItem("Fertig"))
        self._progress.setValue(self._progress.value() + 1)

    def _on_file_error(self, idx: int, msg: str):
        self._table.setItem(idx, 4, QTableWidgetItem(f"Fehler: {msg}"))
        self._progress.setValue(self._progress.value() + 1)

    def _on_all_done(self):
        self._start_btn.setEnabled(True)
        self._cancel_btn.setEnabled(False)
        self._progress.setVisible(False)
        self._status_label.setText("Batch abgeschlossen!")

        if self._results:
            total_orig = sum(r.original_size for r in self._results)
            total_comp = sum(r.compressed_size for r in self._results)
            saved = total_orig - total_comp
            avg_ratio = sum(r.ratio for r in self._results) / len(self._results)
            self._summary_label.setText(
                f"Dateien: {len(self._results)} / {len(self._audio_paths)}\n"
                f"Original gesamt: {total_orig / 1024:.1f} KB\n"
                f"Komprimiert gesamt: {total_comp / 1024:.1f} KB\n"
                f"Eingespart: {saved / 1024:.1f} KB\n"
                f"Durchschnittliche Ratio: {avg_ratio:.1f}x"
            )
            self._summary_group.setVisible(True)

        self._worker = None
