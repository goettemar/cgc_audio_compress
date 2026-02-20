"""Settings tab — default backend, bitrate, output directory."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ... import registry
from ..state import get_state


class SettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_from_config()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # --- Defaults ---
        defaults_group = QGroupBox("Standardeinstellungen")
        defaults_layout = QVBoxLayout(defaults_group)

        # Backend
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Standard-Backend:"))
        self._backend_combo = QComboBox()
        for codec in registry.list_codecs():
            self._backend_combo.addItem(codec.name)
        self._backend_combo.currentTextChanged.connect(self._on_backend_changed)
        row1.addWidget(self._backend_combo, 1)
        defaults_layout.addLayout(row1)

        # Bandwidth
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Standard-Bitrate (kbps):"))
        self._bw_combo = QComboBox()
        self._update_bw_choices()
        row2.addWidget(self._bw_combo, 1)
        defaults_layout.addLayout(row2)

        # LM toggle
        self._lm_check = QCheckBox("Language Model Compression (experimentell)")
        defaults_layout.addWidget(self._lm_check)

        layout.addWidget(defaults_group)

        # --- Output ---
        output_group = QGroupBox("Ausgabe")
        output_layout = QHBoxLayout(output_group)
        output_layout.addWidget(QLabel("Standard-Ausgabeverzeichnis:"))
        self._output_edit = QLineEdit()
        self._output_edit.setPlaceholderText("Kein Standard (neben Quelldatei)")
        output_layout.addWidget(self._output_edit)
        browse_btn = QPushButton("Waehlen")
        browse_btn.setProperty("class", "secondary")
        browse_btn.clicked.connect(self._browse_output)
        output_layout.addWidget(browse_btn)
        layout.addWidget(output_group)

        # --- Save ---
        self._save_btn = QPushButton("Speichern")
        self._save_btn.clicked.connect(self._save)
        layout.addWidget(self._save_btn)

        self._status_label = QLabel("")
        layout.addWidget(self._status_label)

        layout.addStretch()

    def _on_backend_changed(self, _text: str):
        self._update_bw_choices()

    def _update_bw_choices(self):
        self._bw_combo.clear()
        name = self._backend_combo.currentText()
        if not name:
            return
        codec = registry.get(name)
        for spec in codec.default_params():
            if spec.name == "bandwidth":
                self._bw_combo.addItems(spec.choices)
                break

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(self, "Ausgabeverzeichnis waehlen")
        if path:
            self._output_edit.setText(path)

    def _load_from_config(self):
        state = get_state()
        cfg = state.config

        idx = self._backend_combo.findText(cfg.default_backend)
        if idx >= 0:
            self._backend_combo.setCurrentIndex(idx)

        self._update_bw_choices()
        bw_idx = self._bw_combo.findText(cfg.default_bandwidth)
        if bw_idx >= 0:
            self._bw_combo.setCurrentIndex(bw_idx)

        self._lm_check.setChecked(cfg.use_lm)
        self._output_edit.setText(cfg.output_dir)

    def _save(self):
        state = get_state()
        state.config.default_backend = self._backend_combo.currentText()
        state.config.default_bandwidth = self._bw_combo.currentText()
        state.config.use_lm = self._lm_check.isChecked()
        state.config.output_dir = self._output_edit.text().strip()
        state.config.save()
        self._status_label.setText("Einstellungen gespeichert!")
