"""Single-file audio compression tab."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
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
from ...audio_io import get_audio_info
from ...models import ParamType
from ..state import get_state
from ..workers import CompressWorker

AUDIO_FILTER = "Audio (*.wav *.mp3 *.flac *.ogg *.m4a *.aac);;Alle Dateien (*)"


class CompressTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: CompressWorker | None = None
        self._audio_path: Path | None = None
        self._param_widgets: dict[str, QWidget] = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # --- Source file ---
        src_group = QGroupBox("Quelldatei")
        src_layout = QHBoxLayout(src_group)
        self._path_edit = QLineEdit()
        self._path_edit.setReadOnly(True)
        self._path_edit.setPlaceholderText("Audio-Datei waehlen...")
        src_layout.addWidget(self._path_edit)
        self._browse_btn = QPushButton("Durchsuchen")
        self._browse_btn.clicked.connect(self._browse)
        src_layout.addWidget(self._browse_btn)
        layout.addWidget(src_group)

        # --- Audio info ---
        self._info_group = QGroupBox("Audio-Info")
        info_layout = QVBoxLayout(self._info_group)
        self._info_label = QLabel("Keine Datei geladen")
        self._info_label.setWordWrap(True)
        info_layout.addWidget(self._info_label)
        self._info_group.setVisible(False)
        layout.addWidget(self._info_group)

        # --- Backend / params ---
        params_group = QGroupBox("Kompression")
        params_layout = QVBoxLayout(params_group)

        # Backend selector
        row = QHBoxLayout()
        row.addWidget(QLabel("Backend:"))
        self._backend_combo = QComboBox()
        for codec in registry.list_codecs():
            self._backend_combo.addItem(codec.name)
        state = get_state()
        idx = self._backend_combo.findText(state.config.default_backend)
        if idx >= 0:
            self._backend_combo.setCurrentIndex(idx)
        self._backend_combo.currentTextChanged.connect(self._on_backend_changed)
        row.addWidget(self._backend_combo, 1)
        params_layout.addLayout(row)

        # Dynamic param area
        self._param_container = QVBoxLayout()
        params_layout.addLayout(self._param_container)
        self._build_param_widgets()

        layout.addWidget(params_group)

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

        # --- Compress button + progress ---
        action_layout = QHBoxLayout()
        self._compress_btn = QPushButton("Komprimieren")
        self._compress_btn.clicked.connect(self._start_compress)
        self._compress_btn.setEnabled(False)
        action_layout.addWidget(self._compress_btn)
        layout.addLayout(action_layout)

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
        path, _ = QFileDialog.getOpenFileName(self, "Audio-Datei waehlen", start_dir, AUDIO_FILTER)
        if not path:
            return
        self._audio_path = Path(path)
        self._path_edit.setText(path)
        state.config.last_audio_dir = str(self._audio_path.parent)
        state.config.save()
        self._compress_btn.setEnabled(True)
        self._show_info()

    def _show_info(self):
        try:
            info = get_audio_info(self._audio_path)
            mins = int(info.duration // 60)
            secs = info.duration % 60
            self._info_label.setText(
                f"Format: {info.format_name}  |  "
                f"Dauer: {mins}:{secs:05.2f}  |  "
                f"Kanaele: {info.channels}  |  "
                f"Sample-Rate: {info.sample_rate} Hz  |  "
                f"Bitrate: {info.bitrate_kbps:.0f} kbps"
            )
            self._info_group.setVisible(True)
        except Exception as exc:
            self._info_label.setText(f"Fehler: {exc}")
            self._info_group.setVisible(True)

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "Ausgabeverzeichnis waehlen")
        if path:
            self._output_edit.setText(path)

    def _on_backend_changed(self, _text: str):
        self._build_param_widgets()

    def _build_param_widgets(self):
        # Clear old widgets
        while self._param_container.count():
            item = self._param_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget():
                        sub.widget().deleteLater()

        self._param_widgets.clear()
        codec = registry.get(self._backend_combo.currentText())
        for spec in codec.default_params():
            row = QHBoxLayout()
            row.addWidget(QLabel(f"{spec.label}:"))

            if spec.type == ParamType.CHOICE:
                w = QComboBox()
                w.addItems(spec.choices)
                idx = w.findText(str(spec.default))
                if idx >= 0:
                    w.setCurrentIndex(idx)
                # Apply default from settings
                state = get_state()
                if spec.name == "bandwidth":
                    bw_idx = w.findText(state.config.default_bandwidth)
                    if bw_idx >= 0:
                        w.setCurrentIndex(bw_idx)
                row.addWidget(w, 1)
                self._param_widgets[spec.name] = w
            elif spec.type == ParamType.BOOL:
                from PySide6.QtWidgets import QCheckBox
                w = QCheckBox()
                w.setChecked(bool(spec.default))
                row.addWidget(w, 1)
                self._param_widgets[spec.name] = w

            container = QWidget()
            container.setLayout(row)
            self._param_container.addWidget(container)

    def _collect_params(self) -> dict:
        params = {}
        for name, widget in self._param_widgets.items():
            if isinstance(widget, QComboBox):
                params[name] = widget.currentText()
            elif hasattr(widget, "isChecked"):
                params[name] = widget.isChecked()
        return params

    def _start_compress(self):
        if not self._audio_path:
            return

        codec = registry.get(self._backend_combo.currentText())
        params = self._collect_params()

        # Determine output path
        out_dir = self._output_edit.text().strip()
        if out_dir:
            output = Path(out_dir) / self._audio_path.stem
        else:
            output = self._audio_path.parent / self._audio_path.stem

        self._compress_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._progress.setValue(0)
        self._result_group.setVisible(False)
        self._status_label.setText("Komprimiere...")

        self._worker = CompressWorker(codec, self._audio_path, output, params, self)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished_signal.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, msg: str, current: int, total: int):
        self._progress.setMaximum(total)
        self._progress.setValue(current)
        self._status_label.setText(msg)

    def _on_finished(self, result):
        self._compress_btn.setEnabled(True)
        self._progress.setVisible(False)
        self._status_label.setText("Fertig!")

        size_orig_kb = result.original_size / 1024
        size_comp_kb = result.compressed_size / 1024
        self._result_label.setText(
            f"Original: {size_orig_kb:.1f} KB ({result.original_bitrate_kbps:.0f} kbps)\n"
            f"Komprimiert: {size_comp_kb:.1f} KB ({result.compressed_bitrate_kbps:.0f} kbps)\n"
            f"Ratio: {result.ratio:.1f}x\n"
            f"Dauer: {result.duration:.1f}s  |  Encode-Zeit: {result.encode_time:.2f}s\n"
            f"Backend: {result.backend_name}\n"
            f"Ausgabe: {result.compressed_path}"
        )
        self._result_group.setVisible(True)
        self._worker = None

    def _on_error(self, msg: str):
        self._compress_btn.setEnabled(True)
        self._progress.setVisible(False)
        self._status_label.setText(f"Fehler: {msg}")
        self._worker = None
