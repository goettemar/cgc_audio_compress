"""Zentrales Farbschema und Stylesheets — CGC Studio Design."""

COLORS = {
    # Primary
    "teal_dark": "#319795",
    "teal_mid": "#38B2AC",
    "teal_light": "#81E6D9",
    # Secondary
    "purple_dark": "#6B46C1",
    "purple_light": "#B794F4",
    # Neutral
    "bg_primary": "#f8f9fc",
    "bg_card": "#ffffff",
    "text_primary": "#1c2321",
    "text_muted": "#718096",
    "border": "#e2e8f0",
    "border_focus": "#319795",
    # Status
    "success": "#2ecc71",
    "warning": "#f39c12",
    "error": "#e74c3c",
    "info": "#3498db",
}

STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS['bg_primary']};
}}

QTabWidget::pane {{
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    background-color: {COLORS['bg_card']};
    padding: 8px;
}}

QTabBar::tab {{
    background-color: {COLORS['border']};
    color: #4a5568;
    padding: 10px 20px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: 500;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['teal_dark']};
    color: white;
}}

QTabBar::tab:hover:!selected {{
    background-color: #cbd5e0;
}}

QGroupBox {{
    font-weight: bold;
    font-size: 12px;
    color: {COLORS['teal_dark']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    margin-top: 12px;
    padding: 16px 12px 12px 12px;
    background-color: {COLORS['bg_card']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
    left: 12px;
}}

QPushButton {{
    background-color: {COLORS['teal_dark']};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: bold;
    font-size: 12px;
    min-height: 20px;
}}
QPushButton:hover {{
    background-color: {COLORS['teal_mid']};
}}
QPushButton:pressed {{
    background-color: #2C7A7B;
}}
QPushButton:disabled {{
    background-color: #cbd5e0;
    color: #a0aec0;
}}

QPushButton[class="secondary"] {{
    background-color: {COLORS['border']};
    color: {COLORS['text_primary']};
}}
QPushButton[class="secondary"]:hover {{
    background-color: #cbd5e0;
}}

QLineEdit, QTextEdit, QPlainTextEdit {{
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px 10px;
    background-color: {COLORS['bg_card']};
    font-size: 12px;
    color: {COLORS['text_primary']};
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {COLORS['border_focus']};
}}

QComboBox {{
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px 10px;
    background-color: {COLORS['bg_card']};
    font-size: 12px;
    color: {COLORS['text_primary']};
    min-height: 20px;
}}
QComboBox:focus {{
    border-color: {COLORS['border_focus']};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox QAbstractItemView {{
    border: 1px solid {COLORS['border']};
    background-color: {COLORS['bg_card']};
    color: {COLORS['text_primary']};
    selection-background-color: {COLORS['teal_dark']};
    selection-color: white;
    padding: 4px;
    outline: none;
}}

QSpinBox, QDoubleSpinBox {{
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 6px 10px;
    background-color: {COLORS['bg_card']};
    font-size: 12px;
    min-height: 20px;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {COLORS['border_focus']};
}}

QProgressBar {{
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    text-align: center;
    font-size: 11px;
    min-height: 22px;
}}
QProgressBar::chunk {{
    background-color: {COLORS['teal_dark']};
    border-radius: 5px;
}}

QTableWidget {{
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    background-color: {COLORS['bg_card']};
    gridline-color: {COLORS['bg_primary']};
    font-size: 12px;
    outline: none;
}}
QTableWidget::item:selected {{
    background-color: {COLORS['teal_dark']};
    color: white;
}}
QHeaderView::section {{
    background-color: {COLORS['bg_primary']};
    border: none;
    border-bottom: 1px solid {COLORS['border']};
    padding: 6px;
    font-weight: bold;
    font-size: 11px;
}}

QLabel {{
    color: {COLORS['text_primary']};
    font-size: 12px;
}}

QScrollArea {{
    border: none;
    background-color: transparent;
}}
QScrollBar:vertical {{
    width: 8px;
    background: transparent;
}}
QScrollBar::handle:vertical {{
    background: {COLORS['border']};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QCheckBox {{
    font-size: 12px;
    color: {COLORS['text_primary']};
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    background-color: {COLORS['bg_card']};
}}
QCheckBox::indicator:checked {{
    background-color: {COLORS['teal_dark']};
    border-color: {COLORS['teal_dark']};
}}
"""
