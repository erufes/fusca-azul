"""Aspect-preserving video widget with an optional hand overlay."""
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

EDGES = (
	(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8),
	(5, 9), (9, 10), (10, 11), (11, 12), (9, 13), (13, 14), (14, 15),
	(15, 16), (13, 17), (17, 18), (18, 19), (19, 20), (0, 17),
)


class VideoView(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.image = None
		self.landmarks = ()
		self.show_landmarks = True
		self.message = "Preparando câmera…"
		self.setMinimumSize(360, 270)
		self.setAccessibleName("Prévia espelhada da câmera")

	def set_frame(self, image, landmarks):
		self.image, self.landmarks = image, landmarks
		self.update()

	def clear(self, message):
		self.image = None
		self.landmarks = ()
		self.message = message
		self.update()

	def set_landmarks_visible(self, visible):
		self.show_landmarks = visible
		self.update()

	def paintEvent(self, event):
		painter = QPainter(self)
		painter.setRenderHint(QPainter.RenderHint.Antialiasing)
		painter.fillRect(self.rect(), QColor("#111917"))
		if self.image is None:
			painter.setPen(QColor("#a9bab3"))
			painter.drawText(self.rect().adjusted(24, 24, -24, -24), Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, self.message)
			return
		size = self.image.size().scaled(self.size(), Qt.AspectRatioMode.KeepAspectRatio)
		rect = QRectF((self.width() - size.width()) / 2, (self.height() - size.height()) / 2, size.width(), size.height())
		painter.drawImage(rect, self.image)
		if self.show_landmarks and len(self.landmarks) == 21:
			points = [QPointF(rect.x() + x * rect.width(), rect.y() + y * rect.height()) for x, y in self.landmarks]
			painter.setPen(QPen(QColor("#d6e6bc"), 2))
			for start, end in EDGES:
				painter.drawLine(points[start], points[end])
			painter.setBrush(QColor("#b5e0c7"))
			for point in points:
				painter.drawEllipse(point, 4, 4)
