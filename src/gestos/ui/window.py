"""Application window and capture lifecycle; no recognition algorithms."""
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
	QCheckBox, QFrame, QHBoxLayout, QLabel, QMainWindow, QPushButton,
	QSpinBox, QVBoxLayout, QWidget,
)

from ..camera import CameraWorker
from .video import VideoView

COMMANDS = {
	"FRENTE": ("↑", "Em frente"),
	"RE": ("↓", "Para trás"),
	"DIREITA": ("→", "Direita"),
	"ESQUERDA": ("←", "Esquerda"),
	"PARAR": ("■", "Parado"),
	"TROCAR_MODO": ("↔", "Troca de modo"),
	"AGUARDANDO": ("…", "Aguardando"),
	"NENHUMA_MAO": ("—", "Nenhuma mão"),
}


class MainWindow(QMainWindow):
	def __init__(self, *, worker_factory=CameraWorker, auto_start=True):
		super().__init__()
		self.worker_factory = worker_factory
		self.worker = None
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
		layout.addWidget(title)
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
		camera_label = QLabel("Câmera:")
		controls.addWidget(camera_label)
		self.camera = QSpinBox()
		self.camera.setRange(0, 20)
		self.camera.setAccessibleName("Número da câmera")
		self.camera.setToolTip("0 é a câmera padrão. Pause e experimente 1 ou 2 para outra webcam.")
		camera_label.setBuddy(self.camera)
		controls.addWidget(self.camera)
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
		if auto_start:
			QTimer.singleShot(0, self.start_camera)

	def toggle_camera(self):
		if self.worker is None:
			self.start_camera()
		else:
			self.stop_camera()

	def start_camera(self):
		if self.worker is not None or self.closing:
			return
		self.error = None
		self.stopping = False
		self.video.clear("Preparando câmera…")
		self.gesture.setText("Aguardando")
		self.symbol.setText("—")
		self.mode.setText("Modo: Gestos")
		self.camera.setEnabled(False)
		self.button.setText("Pausar câmera")
		self.worker = self.worker_factory(self.camera.value(), self)
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
		self.button.setEnabled(True)
		self.button.setText("Tentar novamente" if self.error else "Ativar câmera")
		self.camera.setEnabled(True)
		self.status.setText(self.error or "Câmera pausada")
		self.video.clear("Não foi possível usar a câmera" if self.error else "Câmera pausada")
		self.gesture.setText("Aguardando")
		self.symbol.setText("—")
		self.mode.setText("Modo: Gestos")
		if self.closing:
			self.close()

	def closeEvent(self, event):
		if self.worker is not None:
			self.closing = True
			self.stop_camera()
			event.ignore()
		else:
			event.accept()
