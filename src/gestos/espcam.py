"""ESP32-CAM discovery and bounded JPEG polling without a buffered video queue."""
import http.client
from threading import Lock
from time import monotonic
from urllib.parse import urlsplit

import cv2
import numpy as np
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage

from .autonomy import DepthNavigator
from .depth import DepthEstimator, depth_model_path, ensure_depth_model

CAMERA_SERVICE = "_fusca-cam._tcp.local."
MAX_JPEG = 160_000
MAX_FRAME_AGE = .4


def discover_camera(cancelled):
	from zeroconf import IPVersion, ServiceBrowser, ServiceListener, Zeroconf

	class Listener(ServiceListener):
		def __init__(self):
			self.names = set()
			self.lock = Lock()

		def add_service(self, zc, type_, name):
			with self.lock:
				self.names.add(name)

		def update_service(self, zc, type_, name):
			self.add_service(zc, type_, name)

		def remove_service(self, zc, type_, name):
			with self.lock:
				self.names.discard(name)

	with Zeroconf(ip_version=IPVersion.V4Only) as zc:
		listener = Listener()
		browser = ServiceBrowser(zc, CAMERA_SERVICE, listener)
		try:
			for _ in range(30):
				if cancelled():
					raise InterruptedError()
				QThread.msleep(100)
			with listener.lock:
				names = list(listener.names)
			if len(names) != 1:
				raise RuntimeError("Nenhuma ESP32-CAM encontrada ou há várias na rede. Informe o endereço da câmera desejada.")
			info = zc.get_service_info(CAMERA_SERVICE, names[0], timeout=1000)
			if info is None or not info.parsed_addresses():
				raise RuntimeError("Não foi possível resolver o endereço da ESP32-CAM.")
			return f"http://{info.parsed_addresses()[0]}:{info.port}/capture"
		finally:
			browser.cancel()


class CameraHTTP:
	def __init__(self, url):
		parsed = urlsplit(url)
		if parsed.scheme != "http" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
			raise ValueError("Use http://endereço-da-câmera/capture")
		self.connection = http.client.HTTPConnection(parsed.hostname, parsed.port or 80, timeout=.6)
		self.path = parsed.path if parsed.path and parsed.path != "/" else "/capture"
		self.last_id = -1

	def read(self):
		started = monotonic()
		self.connection.request("GET", self.path, headers={"Cache-Control": "no-cache"})
		response = self.connection.getresponse()
		if response.status != 200 or response.getheader("Content-Type", "").split(";")[0] != "image/jpeg":
			raise RuntimeError("A ESP32-CAM não retornou uma imagem JPEG.")
		length = int(response.getheader("Content-Length", "0"))
		frame_id = int(response.getheader("X-Fusca-Frame", "-1"))
		age_ms = int(response.getheader("X-Fusca-Age-Ms", "-1"))
		if not 0 < length <= MAX_JPEG or frame_id <= self.last_id or not 0 <= age_ms <= 150:
			raise RuntimeError("Imagem repetida, antiga ou incompatível. Use o firmware ESP32-CAM deste projeto.")
		data = bytearray()
		while len(data) < length:
			if monotonic() - started > .6:
				raise TimeoutError("Transmissão da ESP32-CAM muito lenta")
			chunk = response.read(min(4096, length - len(data)))
			if not chunk:
				raise RuntimeError("Imagem incompleta da ESP32-CAM")
			data.extend(chunk)
		frame = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
		if frame is None or frame.shape[:2] != (240, 320):
			raise RuntimeError("Imagem inválida: esperado vídeo 320 × 240 do firmware ESP32-CAM")
		self.last_id = frame_id
		return frame, started - age_ms / 1000

	def close(self):
		self.connection.close()


class ESPCameraWorker(QThread):
	status = Signal(str)
	failed = Signal(str)

	def __init__(self, url="", parent=None):
		super().__init__(parent)
		self.url = url.strip()
		self._lock = Lock()
		self._latest = None

	def take_frame(self):
		with self._lock:
			frame, self._latest = self._latest, None
			return frame

	def run(self):
		camera = None
		navigator = DepthNavigator()
		try:
			self.status.emit("Procurando ESP32-CAM…" if not self.url else "Conectando à ESP32-CAM…")
			url = self.url or discover_camera(self.isInterruptionRequested)
			if self.isInterruptionRequested():
				return
			path = ensure_depth_model(depth_model_path(), self.status.emit, self.isInterruptionRequested)
			self.status.emit("Preparando análise de profundidade…")
			estimator = DepthEstimator(path)
			camera = CameraHTTP(url)
			while not self.isInterruptionRequested():
				frame, captured = camera.read()
				if monotonic() - captured > MAX_FRAME_AGE:
					raise TimeoutError("Vídeo atrasado. Aproxime o robô do roteador e reconecte.")
				depth = estimator.predict(frame)
				image, heat, navigation = navigator.analyze(frame, depth, monotonic())
				rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
				qimage = QImage(rgb.data, 320, 240, rgb.strides[0], QImage.Format.Format_RGB888).copy()
				heat_rgb = cv2.cvtColor(heat, cv2.COLOR_BGR2RGB)
				heat_image = QImage(heat_rgb.data, 320, 240, heat_rgb.strides[0], QImage.Format.Format_RGB888).copy()
				with self._lock:
					self._latest = (qimage, heat_image, navigation, captured)
				self.msleep(60)
		except InterruptedError:
			pass
		except Exception as error:
			if not self.isInterruptionRequested():
				self.failed.emit(str(error))
		finally:
			if camera is not None:
				camera.close()
