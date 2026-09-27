"""Navigation decisions, image protocol and UI arbitration without hardware."""
import io
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import unittest
from unittest.mock import Mock, patch

import cv2
import numpy as np
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from gestos.autonomy import DepthNavigator, Navigation
from gestos.depth import DepthEstimator
from gestos.espcam import CameraHTTP, ESPCameraWorker
from gestos.network import CommandState
from gestos.ui.autonomous import AutonomousPanel


class NavigationTests(unittest.TestCase):
	def setUp(self):
		self.image = np.full((240, 320, 3), 120, np.uint8)
		self.floor = np.repeat(np.linspace(.1, 1, 240, dtype=np.float32)[:, None], 320, axis=1)
		self.navigator = DepthNavigator()

	def decide(self, depth):
		for t in (0, .1, .2):
			_, _, result = self.navigator.analyze(self.image, depth, t)
		return result

	def test_open_path_requires_stable_frames(self):
		self.assertEqual(self.navigator.analyze(self.image, self.floor, 0)[2].command, "PARAR")
		self.assertEqual(self.decide(self.floor).command, "FRENTE")

	def test_center_obstacle_turns_toward_free_side(self):
		self.floor[125:188, 112:208] += .5
		self.assertEqual(self.decide(self.floor).command, "ESQUERDA")
		self.floor[125:188, 32:112] += .5
		self.assertEqual(self.decide(self.floor).command, "DIREITA")

	def test_near_obstacle_stops_immediately(self):
		self.assertEqual(self.decide(self.floor).command, "FRENTE")
		self.floor[198:228, 96:224] += .5
		self.assertEqual(self.navigator.analyze(self.image, self.floor, .3)[2].command, "PARAR")

	def test_no_floor_flat_depth_dark_and_nonfinite_stop(self):
		for depth in (np.ones((240, 320), np.float32), self.floor[::-1].copy(), self.floor * np.nan):
			result = self.decide(depth)
			self.assertEqual(result.command, "PARAR")
			self.assertFalse(result.confident)
		self.image[:] = 0
		self.assertFalse(self.decide(self.floor).confident)

	def test_turn_is_pulsed_and_gap_requires_confirmation(self):
		self.floor[125:188, 112:208] += .5
		self.assertEqual(self.decide(self.floor).command, "ESQUERDA")
		for t in (.3, .4, .5, .6):
			result = self.navigator.analyze(self.image, self.floor, t)[2]
		self.assertEqual(result.command, "PARAR")
		self.assertEqual(self.navigator.analyze(self.image, self.floor, 1.5)[2].command, "PARAR")

	def test_inverse_depth_scale_and_offset_do_not_change_decision(self):
		self.floor[125:188, 112:208] += .5
		self.assertEqual(self.decide(self.floor * 200 + 100).command, "ESQUERDA")


class CameraProtocolTests(unittest.TestCase):
	def response(self, frame_id="1", age="0", data=None):
		if data is None:
			data = cv2.imencode(".jpg", np.full((240, 320, 3), 100, np.uint8))[1].tobytes()
		response = Mock(status=200)
		headers = {"Content-Type": "image/jpeg", "Content-Length": str(len(data)), "X-Fusca-Frame": frame_id, "X-Fusca-Age-Ms": age}
		response.getheader.side_effect = lambda key, default=None: headers.get(key, default)
		response.read.side_effect = io.BytesIO(data).read
		return response

	@patch("gestos.espcam.http.client.HTTPConnection")
	def test_valid_image_and_replayed_sequence(self, connection):
		connection.return_value.getresponse.side_effect = [self.response(), self.response()]
		camera = CameraHTTP("http://192.168.1.50")
		frame, captured = camera.read()
		self.assertEqual(frame.shape, (240, 320, 3))
		self.assertGreater(captured, 0)
		with self.assertRaises(RuntimeError):
			camera.read()
		camera.close()
		connection.return_value.close.assert_called_once()

	@patch("gestos.espcam.http.client.HTTPConnection")
	def test_old_missing_metadata_and_corrupt_jpeg_rejected(self, connection):
		for response in (self.response(age="200"), self.response(frame_id="-1"), self.response(data=b"not a jpeg")):
			connection.return_value.getresponse.return_value = response
			with self.assertRaises(RuntimeError):
				CameraHTTP("http://camera/capture").read()

	def test_non_http_and_embedded_credentials_rejected(self):
		for url in ("file:///tmp/video", "rtsp://camera", "http://user:password@camera"):
			with self.assertRaises(ValueError):
				CameraHTTP(url)

	@patch("gestos.depth.cv2.dnn.readNetFromONNX")
	def test_model_input_matches_official_onnx_preprocessing(self, read_net):
		read_net.return_value.forward.return_value = np.ones((1, 256, 256), np.float32)
		estimator = DepthEstimator("model.onnx")
		frame = np.zeros((240, 320, 3), np.uint8)
		frame[:, :, 2] = 255
		self.assertEqual(estimator.predict(frame).shape, (240, 320))
		blob = read_net.return_value.setInput.call_args.args[0]
		self.assertEqual(blob.shape, (1, 3, 256, 256))
		self.assertAlmostEqual(float(blob[0, 0].mean()), 1)
		self.assertEqual(float(blob[0, 2].mean()), 0)


class FakeCamera(QObject):
	status = Signal(str)
	failed = Signal(str)
	finished = Signal()

	def __init__(self, url, parent):
		super().__init__(parent)
		self.frame = None
		self.interrupted = False

	def start(self):
		pass

	def take_frame(self):
		frame, self.frame = self.frame, None
		return frame

	def requestInterruption(self):
		self.interrupted = True

	def wait(self):
		return True


class PanelTests(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.app = QApplication.instance() or QApplication([])

	def setUp(self):
		self.now = 10.
		self.state = CommandState(lambda: self.now)
		self.panel = AutonomousPanel(self.state, worker_factory=FakeCamera, clock=lambda: self.now)
		self.settings = patch("gestos.ui.autonomous.QSettings").start()
		self.panel.toggle_connection()
		self.image = QImage(320, 240, QImage.Format.Format_RGB888)
		self.image.fill(0)

	def tearDown(self):
		self.panel.shutdown()
		if self.panel.worker is not None:
			self.panel.worker.finished.emit()
		self.panel.close()
		self.panel.deleteLater()
		patch.stopall()

	def feed(self, command="FRENTE", captured=None):
		self.panel.worker.frame = (self.image, self.image, Navigation(command, command, True), self.now if captured is None else captured)
		self.panel.refresh()

	def test_preview_never_moves_robot_and_activation_requires_connected_robot(self):
		self.feed()
		self.assertFalse(self.panel.set_active(True))
		self.assertEqual(self.state.response(), b"FUSCA/1 PARAR\n")
		self.assertTrue(self.panel.set_active(True))
		self.feed("DIREITA")
		self.assertEqual(self.state.response(), b"FUSCA/1 DIREITA\n")

	def test_stale_video_disarms_and_does_not_rearm_on_return(self):
		self.state.response()
		self.feed()
		self.panel.set_active(True)
		self.feed()
		self.now += .5
		self.panel.refresh()
		self.assertFalse(self.panel.active)
		self.feed()
		self.assertFalse(self.panel.active)
		self.assertEqual(self.state.response(), b"FUSCA/1 PARAR\n")

	def test_stop_disconnect_and_shutdown_invalidate_pending_frame(self):
		self.state.response()
		self.feed()
		self.panel.set_active(True)
		self.feed()
		self.panel.stop_stream()
		self.feed()
		self.assertEqual(self.state.response(), b"FUSCA/1 PARAR\n")
		self.assertTrue(self.panel.worker.interrupted)
		self.assertFalse(self.panel.shutdown())
		self.panel.worker.finished.emit()
		self.assertTrue(self.panel.shutdown())

	def test_old_analysis_cannot_enable_autonomy(self):
		self.state.response()
		self.feed(captured=self.now - 1)
		self.assertFalse(self.panel.set_active(True))
