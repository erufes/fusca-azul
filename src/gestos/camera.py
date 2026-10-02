"""Camera and recognition worker; only the most recent frame is retained."""
import logging
from threading import Lock

import cv2
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

from .detection import GestureDetector
from .devices import CameraDevice
from .model import ensure_model, model_path

logger = logging.getLogger("gestos")


class CameraWorker(QThread):
	status = Signal(str)
	failed = Signal(str)

	def __init__(self, camera_index=0, parent=None):
		super().__init__(parent)
		self.camera_index = camera_index
		self._lock = Lock()
		self._latest = None

	def take_frame(self):
		with self._lock:
			frame, self._latest = self._latest, None
			return frame

	def run(self):
		capture = detector = None
		try:
			path = ensure_model(model_path(), self.status.emit, self.isInterruptionRequested)
			if self.isInterruptionRequested():
				return
			self.status.emit("Preparando reconhecimento…")
			detector = GestureDetector(path)
			if self.isInterruptionRequested():
				return
			self.status.emit("Abrindo câmera…")
			if isinstance(self.camera_index, CameraDevice):
				capture = cv2.VideoCapture(self.camera_index.index, self.camera_index.backend)
			else:
				capture = cv2.VideoCapture(self.camera_index)
			if not capture.isOpened():
				raise RuntimeError(
					"Não foi possível abrir a câmera. Confira a permissão do sistema, "
					"feche outros aplicativos ou escolha outra câmera nas configurações."
				)
			capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
			capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
			capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
			logger.info("Câmera iniciada.")
			self.status.emit("Câmera conectada • reconhecimento local")
			while not self.isInterruptionRequested():
				ok, frame = capture.read()
				if not ok or frame is None:
					raise RuntimeError("A câmera parou de enviar imagens. Reconecte-a e tente novamente.")
				rgb = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
				result = detector.process(rgb)
				height, width, _ = rgb.shape
				image = QImage(rgb.data, width, height, rgb.strides[0], QImage.Format.Format_RGB888).copy()
				with self._lock:
					self._latest = (image, result)
				self.msleep(10)
		except InterruptedError:
			pass
		except Exception as error:
			logger.exception("Falha na captura ou no reconhecimento.")
			if not self.isInterruptionRequested():
				self.failed.emit(str(error) or "Não foi possível iniciar o reconhecimento.")
		finally:
			try:
				if capture is not None:
					capture.release()
			finally:
				if detector is not None:
					detector.close()
			logger.info("Captura encerrada.")
