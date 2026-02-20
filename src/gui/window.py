"""Main window with header and tabs."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter
from PySide6.QtWidgets import (
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .styles import COLORS, STYLESHEET
from .tabs.batch_tab import BatchTab
from .tabs.compress_tab import CompressTab
from .tabs.decompress_tab import DecompressTab
from .tabs.settings_tab import SettingsTab


class _Header(QWidget):
    """Teal gradient header bar."""

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._title = title
        self.setFixedHeight(70)

    def paintEvent(self, event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        grad = QLinearGradient(0, 0, self.width(), 0)
        grad.setColorAt(0, QColor(COLORS["teal_dark"]))
        grad.setColorAt(1, QColor(COLORS["teal_light"]))
        p.fillRect(self.rect(), grad)

        p.setPen(QColor("white"))
        font = QFont()
        font.setPixelSize(22)
        font.setBold(True)
        p.setFont(font)
        p.drawText(
            self.rect().adjusted(24, 0, 0, 0),
            Qt.AlignmentFlag.AlignVCenter,
            self._title,
        )
        p.end()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CGC Audio Compress")
        self.setMinimumSize(900, 700)
        self.resize(1100, 800)
        self.setStyleSheet(STYLESHEET)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(_Header("CGC Audio Compress"))

        tabs = QTabWidget()

        self._compress_tab = CompressTab()
        self._batch_tab = BatchTab()
        self._decompress_tab = DecompressTab()
        self._settings_tab = SettingsTab()

        tabs.addTab(self._compress_tab, "Komprimieren")
        tabs.addTab(self._batch_tab, "Batch")
        tabs.addTab(self._decompress_tab, "Dekomprimieren")
        tabs.addTab(self._settings_tab, "Einstellungen")

        tab_container = QWidget()
        tcl = QVBoxLayout(tab_container)
        tcl.setContentsMargins(12, 12, 12, 12)
        tcl.addWidget(tabs)

        layout.addWidget(tab_container)
