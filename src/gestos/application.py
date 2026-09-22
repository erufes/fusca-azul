"""Desktop startup and logging configuration."""
import logging
import os
import sys

from PySide6.QtWidgets import QApplication

from .ui.theme import STYLE
from .ui.window import MainWindow


def run():
	level = os.environ.get("FUSCA_LOG_LEVEL", "INFO").upper()
	logging.basicConfig(level=getattr(logging, level, logging.INFO))
	app = QApplication(sys.argv)
	app.setApplicationName("Fusca Azul")
	app.setOrganizationName("ERUS")
	app.setStyle("Fusion")
	app.setStyleSheet(STYLE)
	window = MainWindow()
	window.show()
	return app.exec()
