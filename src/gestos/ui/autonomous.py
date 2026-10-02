"""Optional ESP32-CAM video and explicit autonomous-mode controls."""
from time import monotonic

from PySide6.QtCore import QSettings, QTimer, Signal
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from ..espcam import ESPCameraWorker, MAX_FRAME_AGE
from .video import VideoView


class AutonomousPanel(QWidget):
	mode_changed = Signal(bool)
	shutdown_finished = Signal()

	def __init__(self, state=None, parent=None, worker_factory=ESPCameraWorker, clock=monotonic):
		super().__init__(parent)
		self.state, self.worker_factory, self.clock = state, worker_factory, clock
		self.worker = None
		self.active = False
		self.closing = False
		self.stopping = False
		self.last_frame = float("-inf")
		self.navigation = None
		layout = QVBoxLayout(self)
		instructions = QLabel("ESP32-CAM na frente do robô, inclinada para mostrar o piso.\nO vídeo é analisado no computador. Inicie o automático somente após conferir a imagem.")
		instructions.setWordWrap(True)
		layout.addWidget(instructions)
		row = QHBoxLayout()
		self.address = QLineEdit()
		self.address.setPlaceholderText("Automático por mDNS ou http://IP-da-câmera/capture")
		self.address.setAccessibleName("Endereço opcional da ESP32-CAM")
		self.address.setText(QSettings().value("espcam/address", "", str))
		row.addWidget(self.address, 1)
		self.connect_button = QPushButton("Conectar ESP32-CAM")
		self.connect_button.clicked.connect(self.toggle_connection)
		row.addWidget(self.connect_button)
		layout.addLayout(row)
		videos = QHBoxLayout()
		self.video = VideoView()
		self.video.setMinimumSize(280, 180)
		self.video.setAccessibleName("Vídeo frontal da ESP32-CAM com áreas bloqueadas")
		self.video.clear("ESP32-CAM opcional • clique em Conectar")
		self.depth_video = VideoView()
		self.depth_video.setMinimumSize(240, 180)
		self.depth_video.setAccessibleName("Mapa de profundidade relativa")
		self.depth_video.clear("Profundidade relativa • cores claras indicam proximidade")
		videos.addWidget(self.video, 2)
		videos.addWidget(self.depth_video, 1)
		layout.addLayout(videos, 1)
		self.status = QLabel("ESP8266: motores • ESP32-CAM: imagens")
		self.status.setWordWrap(True)
		layout.addWidget(self.status)
		self.decision = QLabel("Automático desativado")
		self.decision.setWordWrap(True)
		layout.addWidget(self.decision)
		row = QHBoxLayout()
		self.start_button = QPushButton("Iniciar automático")
		self.start_button.setEnabled(False)
		self.start_button.clicked.connect(lambda: self.set_active(True))
		row.addWidget(self.start_button)
		self.stop_button = QPushButton("Parar robô / sair do automático")
		self.stop_button.clicked.connect(self.emergency_stop)
		row.addWidget(self.stop_button)
		layout.addLayout(row)
		self.timer = QTimer(self)
		self.timer.timeout.connect(self.refresh)
		self.timer.start(33)

	def set_active(self, active):
		if active and (self.closing or self.stopping or self.worker is None or self.state is None
			or not self.state.connected() or self.clock() - self.last_frame > MAX_FRAME_AGE
			or self.navigation is None or not self.navigation.confident):
			self.status.setText("Para iniciar, conecte o robô e a ESP32-CAM e aguarde uma análise válida do piso.")
			return False
		if self.active != active:
			self.active = active
			if self.state is not None:
				self.state.select_mode("AUTO" if active else "GESTOS")
			self.mode_changed.emit(active)
		if not active:
			self.decision.setText("Automático desativado")
		return True

	def emergency_stop(self):
		self.set_active(False)
		if self.state is not None:
			self.state.update("PARAR")
		# MainWindow also stops gesture capture, preventing its next frame from moving.
		self.mode_changed.emit(False)

	def toggle_connection(self):
		if self.worker is not None:
			self.stop_stream()
			return
		self.stopping = False
		self.navigation = None
		self.last_frame = float("-inf")
		url = self.address.text().strip()
		QSettings().setValue("espcam/address", url)
		self.worker = self.worker_factory(url, self)
		self.worker.status.connect(self.status.setText)
		self.worker.failed.connect(self.stream_error)
		self.worker.finished.connect(self.stream_finished)
		self.address.setEnabled(False)
		self.connect_button.setText("Desconectar ESP32-CAM")
		self.worker.start()

	def stop_stream(self):
		self.set_active(False)
		self.stopping = True
		self.start_button.setEnabled(False)
		self.connect_button.setEnabled(False)
		if self.worker is not None:
			self.worker.requestInterruption()
		self.video.clear("Encerrando transmissão…")
		self.depth_video.clear("Encerrando transmissão…")

	def stream_error(self, message):
		self.status.setText(message)
		self.stop_stream()

	def stream_finished(self):
		self.set_active(False)
		self.worker.wait()
		self.worker.deleteLater()
		self.worker = None
		self.navigation = None
		self.stopping = False
		self.address.setEnabled(True)
		self.connect_button.setEnabled(True)
		self.connect_button.setText("Conectar ESP32-CAM")
		self.video.clear("ESP32-CAM desconectada")
		self.depth_video.clear("Sem profundidade")
		if self.closing:
			self.shutdown_finished.emit()

	def refresh(self):
		frame = self.worker.take_frame() if self.worker is not None and not self.stopping and not self.closing else None
		if frame is not None:
			image, heat, navigation, captured = frame
			self.last_frame, self.navigation = captured, navigation
			age_ms = max(0, int((self.clock() - captured) * 1000))
			self.status.setText(f"ESP32-CAM • idade da análise: {age_ms} ms" + (" • prévia atrasada; automático indisponível" if age_ms > MAX_FRAME_AGE * 1000 else ""))
			self.video.set_frame(image, ())
			self.depth_video.set_frame(heat, ())
			self.decision.setText(("Automático: " if self.active else "Prévia: ") + navigation.reason)
			if self.active and self.state is not None:
				self.state.update_autonomous(navigation.command if navigation.confident else "PARAR", captured)
		fresh = 0 <= self.clock() - self.last_frame <= MAX_FRAME_AGE
		robot_connected = self.state is not None and self.state.connected()
		ready = fresh and robot_connected and self.navigation is not None and self.navigation.confident
		self.start_button.setEnabled(bool(ready and not self.active and not self.stopping and not self.closing))
		if self.active and not robot_connected:
			self.set_active(False)
			self.status.setText("Automático interrompido: robô desconectado. Confira e inicie novamente.")
		elif self.active and not fresh:
			self.state.update_autonomous("PARAR", self.last_frame)
			self.status.setText("Vídeo atrasado: robô parado. O movimento retoma quando chegar uma análise recente e válida.")
			self.decision.setText("Automático: aguardando imagem recente")

	def shutdown(self):
		self.closing = True
		self.timer.stop()
		self.stop_stream()
		return self.worker is None
