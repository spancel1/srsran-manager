"""Dark theme stylesheet for srsRAN Manager."""

DARK_STYLE = """
QMainWindow, QDialog, QWidget {
    background-color: #1a1d23;
    color: #e0e4ed;
    font-family: 'Segoe UI', Consolas, sans-serif;
    font-size: 13px;
}

QSplitter::handle {
    background-color: #2a2d36;
}

/* ── Sidebar panel ── */
#sidebar {
    background-color: #141720;
    border-right: 1px solid #2a2d36;
}

/* ── State buttons ── */
QPushButton#stateBtn {
    background-color: #1e2130;
    color: #9ba3b8;
    border: none;
    border-radius: 6px;
    padding: 8px 14px;
    text-align: left;
    font-size: 13px;
}
QPushButton#stateBtn:hover {
    background-color: #252a3a;
    color: #c8cedf;
}
QPushButton#stateBtn[active="true"] {
    background-color: #1d3461;
    color: #60a0e0;
    font-weight: bold;
}

/* ── Tab bar ── */
QTabWidget::pane {
    border: 1px solid #2a2d36;
    border-radius: 6px;
    background: #1e2130;
}
QTabBar::tab {
    background: #1a1d23;
    color: #6b7390;
    padding: 8px 18px;
    border: none;
    border-bottom: 2px solid transparent;
    margin-right: 2px;
    font-size: 13px;
}
QTabBar::tab:selected {
    color: #60a0e0;
    border-bottom: 2px solid #60a0e0;
    background: #1e2130;
}
QTabBar::tab:hover:!selected {
    color: #a0b0d0;
    background: #1e2130;
}

/* ── Table ── */
QTableWidget {
    background-color: #1a1d23;
    gridline-color: #252835;
    border: none;
    selection-background-color: #1d3461;
    selection-color: #e0e4ed;
    alternate-background-color: #1d2030;
}
QTableWidget::item {
    padding: 4px 8px;
    border: none;
}
QHeaderView::section {
    background-color: #141720;
    color: #6b7390;
    padding: 6px 8px;
    border: none;
    border-bottom: 1px solid #2a2d36;
    font-weight: bold;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ── Form inputs ── */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QTextEdit, QPlainTextEdit {
    background-color: #252a3a;
    color: #c8cedf;
    border: 1px solid #363d52;
    border-radius: 5px;
    padding: 5px 8px;
    selection-background-color: #1d3461;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus,
QComboBox:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border: 1px solid #60a0e0;
}
QComboBox::drop-down {
    border: none;
    width: 22px;
}
QComboBox QAbstractItemView {
    background-color: #252a3a;
    color: #c8cedf;
    selection-background-color: #1d3461;
    border: 1px solid #363d52;
}
QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    background: #363d52;
    border: none;
    width: 18px;
}

/* ── Buttons ── */
QPushButton {
    background-color: #252a3a;
    color: #c0c8e0;
    border: 1px solid #363d52;
    border-radius: 5px;
    padding: 6px 14px;
    font-size: 13px;
}
QPushButton:hover {
    background-color: #2d3448;
    border-color: #60a0e0;
}
QPushButton:pressed {
    background-color: #1d3461;
}
QPushButton#btnPrimary {
    background-color: #1d5494;
    color: #d0e8ff;
    border: 1px solid #2a6db5;
    font-weight: bold;
}
QPushButton#btnPrimary:hover {
    background-color: #2460a8;
}
QPushButton#btnDanger {
    background-color: #5a1a1a;
    color: #ff9090;
    border: 1px solid #8b3030;
}
QPushButton#btnDanger:hover {
    background-color: #6e2020;
}
QPushButton#btnSuccess {
    background-color: #1a4d2e;
    color: #80e8a0;
    border: 1px solid #286640;
    font-weight: bold;
}
QPushButton#btnSuccess:hover {
    background-color: #1f5c37;
}

/* ── Labels ── */
QLabel#heading {
    font-size: 18px;
    font-weight: bold;
    color: #d0daf0;
}
QLabel#subheading {
    font-size: 14px;
    color: #7080a8;
}
QLabel#badge {
    background-color: #1d3461;
    color: #60a0e0;
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: bold;
}

/* ── Group boxes ── */
QGroupBox {
    border: 1px solid #2a2d36;
    border-radius: 7px;
    margin-top: 16px;
    padding-top: 8px;
    color: #7080a8;
    font-size: 12px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    left: 12px;
    top: -1px;
    color: #6090c8;
}

/* ── Scrollbars ── */
QScrollBar:vertical {
    background: #1a1d23;
    width: 8px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #363d52;
    border-radius: 4px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #4a5370;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: #1a1d23;
    height: 8px;
}
QScrollBar::handle:horizontal {
    background: #363d52;
    border-radius: 4px;
    min-width: 20px;
}

/* ── Status bar ── */
QStatusBar {
    background-color: #101318;
    color: #5a6380;
    font-size: 12px;
    border-top: 1px solid #2a2d36;
}
QStatusBar::item {
    border: none;
}

/* ── Toolbar ── */
QToolBar {
    background-color: #141720;
    border-bottom: 1px solid #2a2d36;
    spacing: 6px;
    padding: 4px 8px;
}

/* ── Message boxes ── */
QMessageBox {
    background-color: #1a1d23;
}

/* ── Splitter ── */
QSplitter::handle:horizontal {
    width: 2px;
    background: #252a3a;
}
QSplitter::handle:vertical {
    height: 2px;
    background: #252a3a;
}

/* ── Tooltips ── */
QToolTip {
    background-color: #252a3a;
    color: #c8cedf;
    border: 1px solid #363d52;
    padding: 4px 8px;
    border-radius: 4px;
}

/* ── Progress bar ── */
QProgressBar {
    background: #252a3a;
    border: 1px solid #363d52;
    border-radius: 4px;
    text-align: center;
    color: #8090b8;
}
QProgressBar::chunk {
    background: #1d5494;
    border-radius: 3px;
}
"""
