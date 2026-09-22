"""Qt lifecycle tests with synthetic frames, without camera hardware."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from pathlib import Path
import unittest
from unittest.mock import Mock, patch

import numpy as np
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from gestos.camera import CameraWorker
from gestos.detection import Detection
from gestos.ui.window import MainWindow


class FakeWorker(QObject):
	status = Signal(str)
	failed = Signal(str)
	finished = Signal()

	def __init__(self, index, parent):
		super().__init__(parent)
		self.index = index
		self.interrupted = False
		self.frame = None

	def start(self):
		self.status.emit("Câmera conectada")

	def requestInterruption(self):
		self.interrupted = True

	def take_frame(self):
		frame, self.frame = self.frame, None
		return frame

	def wait(self):
		return True


class WindowTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.app = QApplication.instance() or QApplication([])

	def setUp(self):
		self.window = MainWindow(worker_factory=FakeWorker, auto_start=False)

	def tearDown(self):
		if self.window.worker is not None:
			self.window.worker.finished.emit()
		self.window.close()

	def test_pause_retry_and_camera_selection(self):
		self.window.camera.setValue(2)
		self.window.start_camera()
		worker = self.window.worker
		self.assertEqual(worker.index, 2)
		self.assertFalse(self.window.camera.isEnabled())
		self.window.stop_camera()
		self.assertTrue(worker.interrupted)
		self.assertFalse(self.window.button.isEnabled())
		worker.finished.emit()
		self.assertIsNone(self.window.worker)
		self.assertTrue(self.window.camera.isEnabled())
		self.window.start_camera()
		self.assertIsNot(self.window.worker, worker)

	def test_frame_updates_and_overlay_can_be_disabled(self):
		self.window.start_camera()
		image = QImage(64, 48, QImage.Format.Format_RGB888)
		image.fill(0)
		self.window.worker.frame = (image, Detection("FRENTE", "AUTO", ((.5, .5),) * 21))
		self.window.refresh_frame()
		self.assertEqual(self.window.gesture.text(), "Em frente")
		self.assertEqual(self.window.mode.text(), "Modo: Automático")
		self.window.landmarks.setChecked(False)
		self.assertFalse(self.window.video.show_landmarks)
		self.window.show()
		self.app.processEvents()
		self.assertFalse(self.window.grab().isNull())

	def test_error_is_visible_and_can_be_retried(self):
		self.window.start_camera()
		self.window.worker.failed.emit("Câmera indisponível")
		self.window.worker.finished.emit()
		self.assertEqual(self.window.status.text(), "Câmera indisponível")
		self.assertEqual(self.window.button.text(), "Tentar novamente")
		self.window.start_camera()
		self.assertIsNone(self.window.error)

	def test_close_waits_for_worker_without_destroying_running_thread(self):
		self.window.show()
		self.window.start_camera()
		self.window.close()
		self.assertTrue(self.window.isVisible())
		self.assertTrue(self.window.worker.interrupted)
		self.window.worker.finished.emit()
		self.assertFalse(self.window.isVisible())

	def test_real_thread_stops_and_releases_resources(self):
		capture = Mock()
		capture.read.return_value = (True, np.zeros((32, 32, 3), dtype=np.uint8))
		detector = Mock()
		detector.process.return_value = Detection("PARAR", "GESTOS", ())
		window = MainWindow(auto_start=False)
		with (
			patch("gestos.camera.ensure_model", return_value=Path("model.task")),
			patch("gestos.camera.GestureDetector", return_value=detector),
			patch("gestos.camera.cv2.VideoCapture", return_value=capture),
		):
			try:
				window.start_camera()
				for _ in range(100):
					QTest.qWait(10)
					if window.video.image is not None:
						break
				self.assertIsNotNone(window.video.image)
				window.close()
				for _ in range(100):
					QTest.qWait(10)
					if window.worker is None:
						break
				self.assertIsNone(window.worker)
				capture.release.assert_called_once()
				detector.close.assert_called_once()
			finally:
				if window.worker is not None:
					window.worker.requestInterruption()
					window.worker.wait()
					self.app.processEvents()
				window.close()


class WorkerTests(unittest.TestCase):
	def run_worker(self, capture, detector):
		worker = CameraWorker()
		with patch("gestos.camera.ensure_model", return_value=Path("model.task")):
			with patch("gestos.camera.GestureDetector", return_value=detector):
				with patch("gestos.camera.cv2.VideoCapture", return_value=capture):
					with self.assertLogs("gestos", level="INFO"):
						worker.run()
		return worker

	def test_read_failure_releases_camera_and_detector(self):
		capture = Mock()
		capture.read.return_value = (False, None)
		detector = Mock()
		self.run_worker(capture, detector)
		capture.release.assert_called_once()
		detector.close.assert_called_once()

	def test_latest_frame_owns_pixels_and_is_consumed_once(self):
		capture = Mock()
		capture.read.side_effect = [(True, np.zeros((32, 48, 3), dtype=np.uint8)), (False, None)]
		detector = Mock()
		detector.process.return_value = Detection("PARAR", "GESTOS", ())
		worker = self.run_worker(capture, detector)
		image, result = worker.take_frame()
		self.assertEqual(image.width(), 48)
		self.assertEqual(image.pixelColor(0, 0).red(), 0)
		self.assertEqual(result.command, "PARAR")
		self.assertIsNone(worker.take_frame())
		capture.release.assert_called_once()
		detector.close.assert_called_once()

	def test_detector_failure_still_releases_resources(self):
		capture = Mock()
		capture.read.return_value = (True, np.zeros((8, 8, 3), dtype=np.uint8))
		detector = Mock()
		detector.process.side_effect = RuntimeError("Falha de reconhecimento")
		self.run_worker(capture, detector)
		capture.release.assert_called_once()
		detector.close.assert_called_once()
