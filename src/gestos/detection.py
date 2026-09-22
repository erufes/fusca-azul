"""MediaPipe adapter and gesture session, independent of the interface."""
import logging
from dataclasses import dataclass

from .modes import ModeControl
from .recognition import identificar_comando

logger = logging.getLogger("gestos")


@dataclass(frozen=True)
class Detection:
	command: str
	mode: str
	landmarks: tuple


class GestureDetector:
	def __init__(self, model_path):
		import mediapipe as mp
		from mediapipe.tasks import python
		from mediapipe.tasks.python import vision

		self.mp = mp
		self.detector = vision.HandLandmarker.create_from_options(
			vision.HandLandmarkerOptions(
				base_options=python.BaseOptions(model_asset_path=str(model_path)),
				num_hands=1,
				min_hand_detection_confidence=0.7,
			)
		)
		self.control = ModeControl()
		self.last_command = None

	def process(self, rgb):
		image = self.mp.Image(image_format=self.mp.ImageFormat.SRGB, data=rgb)
		result = self.detector.detect(image)
		points = result.hand_landmarks[0] if result.hand_landmarks else []
		command = identificar_comando(points)
		if self.control.update(command):
			logger.info("Modo selecionado: %s", self.control.mode)
		if command != self.last_command:
			logger.debug("Gesto: %s", command)
			self.last_command = command
		return Detection(command, self.control.mode, tuple((p.x, p.y) for p in points))

	def close(self):
		self.detector.close()
