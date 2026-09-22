"""Named camera discovery using the same backend as video capture."""
import sys
from dataclasses import dataclass

import cv2
from cv2_enumerate_cameras import enumerate_cameras
from PySide6.QtCore import QThread


@dataclass(frozen=True)
class CameraDevice:
	index: int
	backend: int
	name: str
	path: str = ""

	@property
	def key(self):
		return (self.backend, self.path or str(self.index))


def list_cameras():
	backend = {
		"win32": cv2.CAP_DSHOW,
		"darwin": cv2.CAP_AVFOUNDATION,
	}.get(sys.platform, cv2.CAP_V4L2)
	return [
		CameraDevice(camera.index, camera.backend, camera.name, str(camera.path or ""))
		for camera in enumerate_cameras(backend)
	]


class CameraDiscovery(QThread):
	def __init__(self, provider=list_cameras, parent=None):
		super().__init__(parent)
		self.provider = provider
		self.devices = []
		self.error = None

	def run(self):
		try:
			self.devices = self.provider()
		except Exception:
			self.error = "Não foi possível listar as câmeras. Verifique as permissões e tente atualizar."
