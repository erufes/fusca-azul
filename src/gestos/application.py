"""Desktop startup and logging configuration."""
import logging
import os
import sys

from PySide6.QtWidgets import QApplication

from .network import RobotServer
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
	server = RobotServer()
	network_error = None
	try:
		server.start()
	except Exception as exc:
		logging.getLogger(__name__).exception("Não foi possível iniciar o servidor do robô")
		network_error = str(exc)
	window = MainWindow(command_state=server.state, network_error=network_error)
	window.show()
	try:
		return app.exec()
	finally:
		server.close()
