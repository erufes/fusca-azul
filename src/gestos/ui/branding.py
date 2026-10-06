"""Shared application icon, bundled with the installed package."""
from pathlib import Path

from PySide6.QtGui import QIcon


def application_icon():
	return QIcon(str(Path(__file__).parent / "assets" / "logo.svg"))
