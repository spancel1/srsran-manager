#!/usr/bin/env python3
"""srsRAN Manager — US LTE Base Station Profile Manager.

Entry point. Run:
    python main.py
"""
import sys
import os

# Make sure the project root is on the path when run directly
sys.path.insert(0, os.path.dirname(__file__))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from ui.main_window import MainWindow
from ui.styles import DARK_STYLE


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("srsRAN Manager")
    app.setOrganizationName("SRSTools")
    app.setApplicationVersion("1.0.0")

    # HiDPI support
    app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    # Apply dark stylesheet
    app.setStyleSheet(DARK_STYLE)

    # Base font
    font = QFont("Segoe UI", 11)
    app.setFont(font)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
