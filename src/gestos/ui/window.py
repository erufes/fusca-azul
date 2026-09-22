"""Application window and capture lifecycle; no recognition algorithms."""
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
	QCheckBox, QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton,
	QVBoxLayout, QWidget,
)

from ..camera import CameraWorker
from .video import VideoView
from .settings import SettingsDialog
from ..devices import list_cameras

from .gestures import COMMANDS
from .tutorial import TutorialDialog


class MainWindow(QMainWindow):
	def __init__(self, *, worker_factory=CameraWorker, auto_start=True, camera_provider=list_cameras):
		super().__init__()
		self.worker_factory = worker_factory
		self.worker = None
		self.current_device = None
		self.restart_camera = False
		self.auto_start = auto_start
		self.tutorial = TutorialDialog(self)
		self.settings = SettingsDialog(self, camera_provider)
		self.settings.devices_ready.connect(self.devices_ready)
		self.settings.accepted.connect(self.apply_camera)
		self.closing = False
		self.stopping = False
		self.error = None
		self.setWindowTitle("Fusca Azul — Gestos")
		self.resize(1060, 720)
		self.setMinimumSize(800, 600)
		body = QWidget()
		self.setCentralWidget(body)
		layout = QVBoxLayout(body)
		layout.setContentsMargins(28, 24, 28, 24)
		layout.setSpacing(18)
		title = QLabel("Fusca Azul")
		title.setObjectName("title")
		header = QHBoxLayout()
		header.addWidget(title)
		header.addStretch()
		self.help_button = QPushButton("?")
		self.help_button.setObjectName("helpButton")
		self.help_button.setFixedSize(44, 44)
		self.help_button.setAccessibleName("Tutorial")
		self.help_button.setToolTip("Tutorial de gestos e do robô (F1)")
		self.help_button.setShortcut("F1")
		self.help_button.clicked.connect(self.show_tutorial)
		header.addWidget(self.help_button)
		self.settings_button = QPushButton("⚙")
		self.settings_button.setObjectName("settingsButton")
		self.settings_button.setFixedSize(44, 44)
		self.settings_button.setAccessibleName("Configurações")
		self.settings_button.setToolTip("Configurações da câmera")
		self.settings_button.clicked.connect(self.settings.open)
		header.addWidget(self.settings_button)
		layout.addLayout(header)
		self.status = QLabel("Pronto para iniciar")
		self.status.setObjectName("muted")
		self.status.setWordWrap(True)
		layout.addWidget(self.status)
		content = QHBoxLayout()
		content.setSpacing(20)
		self.video = VideoView()
		content.addWidget(self.video, 3)
		card = QFrame()
		card.setObjectName("card")
		card.setMinimumWidth(240)
		panel = QVBoxLayout(card)
		panel.setContentsMargins(24, 24, 24, 24)
		panel.addWidget(QLabel("GESTO RECONHECIDO"))
		self.symbol = QLabel("—")
		self.symbol.setObjectName("symbol")
		panel.addWidget(self.symbol)
		self.gesture = QLabel("Aguardando")
		self.gesture.setObjectName("gesture")
		self.gesture.setWordWrap(True)
		panel.addWidget(self.gesture)
		self.mode = QLabel("Modo: Gestos")
		panel.addWidget(self.mode)
		panel.addStretch()
		help_text = QLabel("Para trocar o modo, mantenha o gesto de rock por 1 segundo.\n\nDesfaça o gesto antes de trocar novamente.")
		help_text.setWordWrap(True)
		help_text.setObjectName("muted")
		panel.addWidget(help_text)
		content.addWidget(card, 1)
		layout.addLayout(content, 1)
		controls = QHBoxLayout()
		self.button = QPushButton("Ativar câmera")
		self.button.clicked.connect(self.toggle_camera)
		controls.addWidget(self.button)
		controls.addStretch()
		self.landmarks = QCheckBox("Pontos da mão")
		self.landmarks.setChecked(True)
		self.landmarks.toggled.connect(self.video.set_landmarks_visible)
		controls.addWidget(self.landmarks)
		layout.addLayout(controls)
		guide = QLabel("Mão aberta: frente  •  Punho: parar  •  V: ré  •  Mindinho: direita  •  Polegar: esquerda")
		guide.setWordWrap(True)
		guide.setObjectName("muted")
		layout.addWidget(guide)
		footer = QLabel("Reconhecimento local • O controle dos motores ainda não está integrado.")
		footer.setObjectName("muted")
		footer.setWordWrap(True)
		layout.addWidget(footer)
		self.timer = QTimer(self)
		self.timer.setInterval(33)
		self.timer.timeout.connect(self.refresh_frame)
		self.button.setEnabled(False)
		self.status.setText("Buscando câmeras…")
		self.settings.scan()

	def show_tutorial(self):
		self.tutorial.show()
		self.tutorial.raise_()
		self.tutorial.activateWindow()

	def devices_ready(self):
		if self.closing:
			self.close()
			return
		device = self.settings.applied_device
		if device is None:
			device = self.settings.camera.currentData()
			self.settings.applied_device = device
		if self.worker is None:
			self.button.setEnabled(device is not None)
			self.status.setText("Pronto para iniciar" if device else self.settings.message.text())
			if device is None:
				self.video.clear("Nenhuma câmera encontrada. Abra as configurações para atualizar a lista.")
		if self.auto_start:
			self.auto_start = False
			if device is not None:
				self.start_camera()

	def apply_camera(self):
		device = self.settings.applied_device
		if self.worker is None:
			self.button.setEnabled(device is not None)
			self.status.setText(f"Câmera selecionada: {device.name}")
		elif device != self.current_device:
			self.restart_camera = True
			self.stop_camera()

	def toggle_camera(self):
		if self.worker is None:
			self.start_camera()
		else:
			self.stop_camera()

	def start_camera(self):
		if self.worker is not None or self.closing or self.settings.applied_device is None:
			return
		self.error = None
		self.stopping = False
		self.video.clear("Preparando câmera…")
		self.gesture.setText("Aguardando")
		self.symbol.setText("—")
		self.mode.setText("Modo: Gestos")
		self.button.setText("Pausar câmera")
		self.current_device = self.settings.applied_device
		self.worker = self.worker_factory(self.current_device, self)
		self.worker.status.connect(self.show_status)
		self.worker.failed.connect(self.show_error)
		self.worker.finished.connect(self.capture_finished)
		self.timer.start()
		self.worker.start()

	def show_status(self, message):
		if not self.stopping:
			self.status.setText(message)

	def show_error(self, message):
		self.error = message
		self.status.setText(message)

	def refresh_frame(self):
		if self.worker is None or self.stopping:
			return
		frame = self.worker.take_frame()
		if frame is None:
			return
		image, result = frame
		self.video.set_frame(image, result.landmarks)
		symbol, label = COMMANDS.get(result.command, COMMANDS["AGUARDANDO"])
		self.symbol.setText(symbol)
		self.gesture.setText(label)
		self.mode.setText("Modo: Automático" if result.mode == "AUTO" else "Modo: Gestos")

	def stop_camera(self):
		if self.worker is None:
			return
		self.stopping = True
		self.timer.stop()
		self.button.setEnabled(False)
		self.status.setText("Encerrando captura…")
		self.video.clear("Encerrando captura…")
		self.gesture.setText("Aguardando")
		self.symbol.setText("—")
		self.worker.requestInterruption()

	def capture_finished(self):
		self.timer.stop()
		self.worker.wait()
		self.worker.deleteLater()
		self.worker = None
		self.stopping = False
		self.button.setEnabled(self.settings.applied_device is not None)
		self.button.setText("Tentar novamente" if self.error else "Ativar câmera")
		self.status.setText(self.error or "Câmera pausada")
		self.video.clear("Não foi possível usar a câmera" if self.error else "Câmera pausada")
		self.gesture.setText("Aguardando")
		self.symbol.setText("—")
		self.mode.setText("Modo: Gestos")
		if self.closing:
			self.close()
		elif self.restart_camera:
			self.restart_camera = False
			self.start_camera()

	def closeEvent(self, event):
		self.closing = True
		self.restart_camera = False
		if self.worker is not None or self.settings.scanner is not None:
			self.stop_camera()
			event.ignore()
		else:
			event.accept()
