"""In-app tutorial, separate from capture and recognition logic."""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
	QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
	QScrollArea, QTabWidget, QVBoxLayout, QWidget,
)

from ..modes import ModeControl
from .gestures import GESTURES


class HandDiagram(QWidget):
	"""Small schematic of extended and folded fingers, drawn without assets."""
	def __init__(self, gesture, parent=None):
		super().__init__(parent)
		self.fingers = gesture.fingers
		self.setFixedSize(86, 110)
		self.setAccessibleName(gesture.pose)
		self.setToolTip("Ilustração esquemática: " + gesture.pose)

	def paintEvent(self, event):
		painter = QPainter(self)
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)
		painter.setPen(QPen(QColor("#a9bab3"), 1.5))
		painter.setBrush(QColor("#34443c"))
		painter.drawRoundedRect(QRectF(27, 52, 48, 44), 12, 12)
		painter.drawRoundedRect(QRectF(35, 85, 32, 22), 5, 5)
		for index, extended in enumerate(self.fingers[1:]):
			x = 28 + index * 12
			top = (18, 8, 15, 29)[index] if extended else 52
			painter.setBrush(QColor("#d6e6bc" if extended else "#526258"))
			painter.drawRoundedRect(QRectF(x, top, 10, 66 - top), 5, 5)
		painter.save()
		painter.translate(30, 75)
		painter.rotate(-48 if self.fingers[0] else 40)
		painter.setBrush(QColor("#d6e6bc" if self.fingers[0] else "#526258"))
		painter.drawRoundedRect(QRectF(-5, -34 if self.fingers[0] else -17, 12, 38 if self.fingers[0] else 22), 6, 6)
		painter.restore()


def paragraph(text, style=None):
	label = QLabel(text)
	label.setWordWrap(True)
	label.setTextFormat(Qt.TextFormat.PlainText)
	if style:
		label.setObjectName(style)
	return label


def section(layout, title, text):
	layout.addWidget(paragraph(title, "tutorialHeading"))
	layout.addWidget(paragraph(text))


def scroll_page():
	area = QScrollArea()
	area.setWidgetResizable(True)
	area.setFrameShape(QFrame.Shape.NoFrame)
	body = QWidget()
	layout = QVBoxLayout(body)
	layout.setContentsMargins(16, 18, 16, 18)
	layout.setSpacing(14)
	area.setWidget(body)
	return area, layout


class TutorialDialog(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setWindowTitle("Tutorial — Fusca Azul")
		self.resize(780, 740)
		self.setMinimumSize(620, 460)
		layout = QVBoxLayout(self)
		layout.setContentsMargins(24, 20, 24, 20)
		layout.setSpacing(16)
		layout.addWidget(paragraph("Conheça o Fusca Azul", "title"))
		layout.addWidget(paragraph("Aprenda os gestos e acompanhe o que o robô já faz nesta versão.", "muted"))
		self.tabs = QTabWidget()
		layout.addWidget(self.tabs, 1)
		self.tabs.addTab(self.gestures_page(), "Gestos e controles")
		self.tabs.addTab(self.robot_page(), "Como funciona o robô")
		footer = QHBoxLayout()
		footer.addWidget(paragraph("Você pode manter este guia aberto enquanto pratica.", "muted"), 1)
		close = QPushButton("Fechar tutorial")
		close.clicked.connect(self.close)
		footer.addWidget(close)
		layout.addLayout(footer)

	def gestures_page(self):
		page, layout = scroll_page()
		section(layout, "1. Prepare a câmera", "A câmera inicia ao abrir o aplicativo. Se precisar trocá-la, use a engrenagem, escolha o nome da câmera e clique em Aplicar. Use Atualizar lista após conectar uma webcam.")
		section(layout, "2. Mostre uma mão", "Mantenha a palma voltada para a câmera e a mão inteira dentro do vídeo. Use boa iluminação. A imagem é espelhada, como um espelho; você pode usar a mão direita ou esquerda.")
		layout.addWidget(paragraph("3. Experimente os gestos", "tutorialHeading"))
		layout.addWidget(paragraph("Os dedos claros nas ilustrações ficam estendidos. O resultado aparece no painel de reconhecimento.", "muted"))
		grid = QGridLayout()
		grid.setSpacing(12)
		grid.setColumnStretch(0, 1)
		grid.setColumnStretch(1, 1)
		for index, gesture in enumerate(GESTURES):
			card = QFrame()
			card.setObjectName("card")
			row = QHBoxLayout(card)
			row.setContentsMargins(12, 12, 12, 12)
			row.addWidget(HandDiagram(gesture))
			text = QVBoxLayout()
			text.addWidget(paragraph(f"{gesture.symbol}  {gesture.label}", "tutorialHeading"))
			text.addWidget(paragraph(gesture.pose))
			row.addLayout(text, 1)
			grid.addWidget(card, index // 2, index % 2)
		layout.addLayout(grid)
		hold = f"{ModeControl.HOLD_SECONDS:g}".replace(".", ",")
		release = f"{ModeControl.RELEASE_SECONDS:g}".replace(".", ",")
		section(layout, "Trocar entre Gestos e Automático", f"Mantenha o rock por {hold} segundo para alternar o modo. Depois, desfaça o gesto por pelo menos {release} segundo antes de repetir. Manter o rock não provoca trocas seguidas. Pausar ou trocar a câmera inicia uma nova sessão em modo Gestos ao retomar a captura.")
		section(layout, "Entenda os controles", "Pontos da mão mostra ou oculta os 21 pontos usados no reconhecimento. Pausar câmera interrompe a captura e libera a webcam. Ativar câmera retoma a captura.")
		section(layout, "Se o gesto não for reconhecido", "Nenhuma mão significa que a câmera não detectou uma mão. Aguardando significa que a pose não corresponde a um comando conhecido. Ajuste o enquadramento, a iluminação e a posição dos dedos. Se a câmera falhar, confira a permissão do sistema, feche outros aplicativos que a usam e tente novamente.")
		layout.addStretch()
		return page

	def robot_page(self):
		page, layout = scroll_page()
		section(layout, "O que é o Fusca Azul?", "É o projeto de robô móvel da ERUS/UFES. O software e o hardware estão sendo atualizados. A proposta é usar gestos para indicar movimentos e oferecer um modo de navegação automática.")
		section(layout, "Da sua mão ao comando", "A webcam captura a imagem. No próprio computador, o reconhecimento localiza 21 pontos da mão e compara a posição dos dedos com os gestos conhecidos. A interface mostra o comando identificado e o modo selecionado. As imagens não são enviadas para um servidor.")
		section(layout, "O que os modos significam", "Gestos representa o controle por comandos da mão: frente, ré, esquerda, direita e parar. Automático representa a proposta de navegação autônoma. Nesta versão, a troca muda apenas o modo exibido no aplicativo.")
		status = QFrame()
		status.setObjectName("card")
		status_layout = QVBoxLayout(status)
		status_layout.setContentsMargins(18, 18, 18, 18)
		section(status_layout, "Estado atual: reconhecimento, sem movimento", "Os comandos ainda não são enviados ao robô. O controle dos motores e a navegação autônoma não estão integrados. Fazer um gesto, selecionar Automático ou fechar o punho não movimenta nem freia fisicamente o robô nesta versão.")
		layout.addWidget(status)
		section(layout, "O que já roda no robô", "O firmware da placa NodeMCU/ESP8266 lê a distância medida pelo sensor VL53L0X e mostra o resultado no monitor serial, em milímetros e centímetros. Essa medição ainda não aparece no aplicativo e ainda não é usada para desviar de obstáculos.")
		section(layout, "Uso sem internet", "Depois de instalar as dependências e baixar o modelo de reconhecimento na primeira execução, a captura e o reconhecimento funcionam localmente. Não é necessário navegador ou configuração de HTTPS.")
		layout.addStretch()
		return page
