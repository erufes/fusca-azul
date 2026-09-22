from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from gestos.detection import GestureDetector
from gestos.modes import ModeControl
from test_recognition import hand


def detector_for(poses):
	detector = GestureDetector.__new__(GestureDetector)
	detector.mp = SimpleNamespace(Image=Mock(), ImageFormat=SimpleNamespace(SRGB=1))
	detector.detector = Mock()
	detector.detector.detect.side_effect = [
		SimpleNamespace(hand_landmarks=[pose] if pose else []) for pose in poses
	]
	detector.control = ModeControl()
	detector.last_command = None
	return detector


class DetectionTests(unittest.TestCase):
	def test_all_gestures_and_missing_hand(self):
		poses = [hand(1, 1, 1, 1, 1), hand(0, 0, 0, 0, 1), hand(1),
			hand(0, 1, 1), hand(), hand(0, 1, 0, 0, 1), []]
		detector = detector_for(poses)
		results = [detector.process(None) for _ in poses]
		self.assertEqual([r.command for r in results],
			["FRENTE", "DIREITA", "ESQUERDA", "RE", "PARAR", "TROCAR_MODO", "NENHUMA_MAO"])
		self.assertEqual([len(r.landmarks) for r in results], [21] * 6 + [0])

	def test_mode_changes_once_and_new_session_resets(self):
		detector = detector_for([hand(0, 1, 0, 0, 1)] * 31)
		with patch("gestos.modes.monotonic", side_effect=[i / 10 for i in range(31)]):
			with self.assertLogs("gestos", level="INFO") as logs:
				results = [detector.process(None) for _ in range(31)]
		self.assertEqual(results[0].mode, "GESTOS")
		self.assertEqual(results[-1].mode, "AUTO")
		self.assertEqual(len(logs.records), 1)
		self.assertEqual(detector_for([[]]).process(None).mode, "GESTOS")

	def test_repeated_frames_only_log_changes(self):
		detector = detector_for([[]] * 100)
		with self.assertLogs("gestos", level="DEBUG") as logs:
			for _ in range(100):
				detector.process(None)
		self.assertEqual(len(logs.records), 1)
		detector.close()
		detector.detector.close.assert_called_once()
