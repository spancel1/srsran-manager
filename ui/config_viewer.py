"""Config preview dialog."""
from __future__ import annotations
import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QPlainTextEdit,
    QPushButton, QLabel, QFileDialog, QMessageBox
)
from PyQt6.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtCore import Qt, QRegularExpression
from core.config_generator import generate_enb_conf, generate_rr_conf, generate_sib_conf, generate_ue_conf


class IniHighlighter(QSyntaxHighlighter):
    """Minimal syntax highlighter for INI / libconfig style."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules: list[tuple[QRegularExpression, QTextCharFormat]] = []

        def fmt(color: str, bold=False) -> QTextCharFormat:
            f = QTextCharFormat()
            f.setForeground(QColor(color))
            if bold:
                f.setFontWeight(700)
            return f

        # Comments  # or //
        self._rules.append((QRegularExpression(r"(#|//).*"), fmt("#5e7040")))
        # Section headers [...]
        self._rules.append((QRegularExpression(r"^\[[^\]]+\]"), fmt("#60a0e0", bold=True)))
        # Keys
        self._rules.append((QRegularExpression(r"^\s*[\w_][\w\d_]*\s*="), fmt("#c8a860")))
        # Strings
        self._rules.append((QRegularExpression(r'"[^"]*"'), fmt("#80c080")))
        # Numbers/hex
        self._rules.append((QRegularExpression(r"\b(0x[0-9a-fA-F]+|\d+\.?\d*)\b"), fmt("#e08050")))

    def highlightBlock(self, text: str) -> None:
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                m = it.next()
                self.setFormat(m.capturedStart(), m.capturedLength(), fmt)


class ConfigViewerDialog(QDialog):
    """Preview and export srsRAN config files for a tower."""
    def __init__(self, tower: dict, sim: dict | None = None, parent=None):
        super().__init__(parent)
        self._tower = tower
        self._sim = sim
        self.setWindowTitle(f"Config — {tower['name']}")
        self.setMinimumSize(820, 600)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(10)

        # Header
        hdr = QLabel(f"<b>{self._tower['name']}</b>  "
                     f"<span style='color:#7080a8'>Band {self._tower['band']} · "
                     f"EARFCN {self._tower['dl_earfcn']} · PCI {self._tower['pci']}</span>")
        hdr.setObjectName("heading")
        layout.addWidget(hdr)

        # Tabs
        tabs = QTabWidget()
        mono = QFont("Consolas", 11)

        self._editors: dict[str, QPlainTextEdit] = {}

        configs = {
            "enb.conf": generate_enb_conf(self._tower),
            "rr.conf":  generate_rr_conf(self._tower),
            "sib.conf": generate_sib_conf(self._tower),
        }
        if self._sim:
            configs["ue.conf"] = generate_ue_conf(self._sim, self._tower)

        for name, content in configs.items():
            editor = QPlainTextEdit(content)
            editor.setFont(mono)
            editor.setReadOnly(False)
            IniHighlighter(editor.document())
            self._editors[name] = editor
            tabs.addTab(editor, name)

        layout.addWidget(tabs, 1)

        # Buttons
        btn_row = QHBoxLayout()
        btn_export_all = QPushButton("Export all to folder…")
        btn_export_all.setObjectName("btnPrimary")
        btn_export_all.clicked.connect(self._export_all)

        btn_copy = QPushButton("Copy current tab")
        btn_copy.clicked.connect(lambda: self._copy_current(tabs))

        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self.accept)

        btn_row.addWidget(btn_export_all)
        btn_row.addWidget(btn_copy)
        btn_row.addStretch()
        btn_row.addWidget(btn_close)
        layout.addLayout(btn_row)

    def _export_all(self):
        folder = QFileDialog.getExistingDirectory(self, "Select export folder")
        if not folder:
            return
        for name, editor in self._editors.items():
            path = os.path.join(folder, name)
            with open(path, "w", encoding="utf-8") as f:
                f.write(editor.toPlainText())
        QMessageBox.information(
            self, "Exported",
            f"Saved {len(self._editors)} file(s) to:\n{folder}"
        )

    def _copy_current(self, tabs: QTabWidget):
        idx = tabs.currentIndex()
        name = tabs.tabText(idx)
        editor = self._editors.get(name)
        if editor:
            from PyQt6.QtWidgets import QApplication
            QApplication.clipboard().setText(editor.toPlainText())
