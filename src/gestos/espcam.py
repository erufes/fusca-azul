"""ESP32-CAM discovery and bounded JPEG polling without a buffered video queue."""
import http.client
import logging
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
logger = logging.getLogger(__name__)


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
		content_type = response.getheader("Content-Type", "").split(";")[0].strip().lower()
		if response.status != 200 or content_type != "image/jpeg":
			detail = ""
			if content_type == "text/plain":
				try:
					detail = " ".join(response.read(512).decode("utf-8", errors="replace").split())
				except (OSError, http.client.HTTPException):
					pass
			message = f"ESP32-CAM: HTTP {response.status} em {self.path} ({content_type or 'sem tipo de conteúdo'})."
			if detail:
				message += f" {detail}"
			elif content_type == "text/html":
				message += " Recebida uma página HTML; confira o endereço /capture e a configuração Wi-Fi da câmera."
			raise RuntimeError(message)
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
			logger.info("ESP32-CAM localizada em %s", url)
			if self.isInterruptionRequested():
				return
			path = ensure_depth_model(depth_model_path(), self.status.emit, self.isInterruptionRequested)
			self.status.emit("Preparando análise de profundidade…")
			estimator = DepthEstimator(path)
			camera = CameraHTTP(url)
			was_slow = False
			while not self.isInterruptionRequested():
				started = monotonic()
				frame, captured = camera.read()
				received = monotonic()
				depth = estimator.predict(frame)
				image, heat, navigation = navigator.analyze(frame, depth, monotonic())
				analyzed = monotonic()
				slow = analyzed - captured > MAX_FRAME_AGE
				if slow and not was_slow:
					logger.warning("Prévia atrasada: captura/transferência %.0f ms; análise %.0f ms; idade total %.0f ms. Movimento bloqueado até uma análise recente.",
						(received - started) * 1000, (analyzed - received) * 1000, (analyzed - captured) * 1000)
				was_slow = slow
				# Keep preview available; the UI and command server reject stale motion.
				# Preserve the original timestamp even when a slow frame is displayed.
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
				logger.warning("Falha na ESP32-CAM: %s", error)
				self.failed.emit(str(error))
		finally:
			if camera is not None:
				camera.close()
