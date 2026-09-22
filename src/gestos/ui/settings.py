"""Camera settings and asynchronous device discovery."""
from collections import Counter

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
	QComboBox, QDialog, QDialogButtonBox, QHBoxLayout, QLabel,
	QPushButton, QVBoxLayout,
)

from ..devices import CameraDiscovery, list_cameras


class SettingsDialog(QDialog):
	devices_ready = Signal()

	def __init__(self, parent=None, provider=list_cameras):
		super().__init__(parent)
		self.provider = provider
		self.scanner = None
		self.applied_device = None
		self.setWindowTitle("Configurações — Fusca Azul")
		self.setMinimumWidth(460)
		layout = QVBoxLayout(self)
		layout.setContentsMargins(24, 24, 24, 24)
		layout.setSpacing(16)
		title = QLabel("Câmera")
		title.setObjectName("title")
		layout.addWidget(title)
		self.camera = QComboBox()
		self.camera.setAccessibleName("Câmera selecionada")
		self.camera.setMinimumContentsLength(24)
		self.camera.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
		layout.addWidget(self.camera)
		self.refresh = QPushButton("Atualizar lista")
		self.refresh.clicked.connect(self.scan)
		row = QHBoxLayout()
		row.addWidget(self.refresh)
		row.addStretch()
		layout.addLayout(row)
		self.message = QLabel("Buscando câmeras…")
		self.message.setWordWrap(True)
		self.message.setObjectName("muted")
		layout.addWidget(self.message)
		buttons = QDialogButtonBox()
		self.apply = buttons.addButton("Aplicar", QDialogButtonBox.ButtonRole.AcceptRole)
		buttons.addButton("Cancelar", QDialogButtonBox.ButtonRole.RejectRole)
		buttons.accepted.connect(self.accept)
		buttons.rejected.connect(self.reject)
		layout.addWidget(buttons)

	def scan(self):
		if self.scanner is not None:
			return
		self.camera.setEnabled(False)
		self.apply.setEnabled(False)
		self.refresh.setEnabled(False)
		self.message.setText("Buscando câmeras…")
		self.scanner = CameraDiscovery(self.provider, self)
		self.scanner.finished.connect(self.scan_finished)
		self.scanner.start()

	def scan_finished(self):
		self.scanner.wait()
		previous = self.camera.currentData() or self.applied_device
		devices, error = self.scanner.devices, self.scanner.error
		self.scanner.deleteLater()
		self.scanner = None
		self.camera.clear()
		names = Counter(device.name for device in devices)
		occurrences = Counter()
		selected = 0
		for index, device in enumerate(devices):
			name = device.name or "Câmera"
			occurrences[device.name] += 1
			if names[device.name] > 1:
				name += f" ({occurrences[device.name]})"
			self.camera.addItem(name, device)
			if previous is not None and device.key == previous.key:
				selected = index
		if not devices:
			self.camera.addItem("Nenhuma câmera encontrada", None)
		self.camera.setCurrentIndex(selected)
		self.camera.setEnabled(bool(devices))
		self.apply.setEnabled(bool(devices))
		self.refresh.setEnabled(True)
		self.message.setText(error or (
			"Escolha uma câmera e clique em Aplicar. A captura ativa será reiniciada."
			if devices else "Conecte uma câmera e clique em Atualizar lista."
		))
		# Preserve the applied device's identity if its capture index changed.
		if self.applied_device is not None:
			self.applied_device = next(
				(device for device in devices if device.key == self.applied_device.key), None
			)
		self.devices_ready.emit()

	def open(self):
		if self.applied_device is not None:
			for index in range(self.camera.count()):
				device = self.camera.itemData(index)
				if device is not None and device.key == self.applied_device.key:
					self.camera.setCurrentIndex(index)
					break
		super().open()

	def accept(self):
		if self.scanner is not None or self.camera.currentData() is None:
			return
		self.applied_device = self.camera.currentData()
		super().accept()
