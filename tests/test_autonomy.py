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

	@patch("gestos.espcam.http.client.HTTPConnection")
	def test_camera_error_preserves_http_status_and_firmware_reason(self, connection):
		response = Mock(status=503)
		response.getheader.return_value = "text/plain; charset=utf-8"
		response.read.return_value = b"Camera indisponivel"
		connection.return_value.getresponse.return_value = response
		with self.assertRaisesRegex(RuntimeError, "HTTP 503.*Camera indisponivel"):
			CameraHTTP("http://camera/capture").read()
		response.read.assert_called_once_with(512)

	@patch("gestos.espcam.http.client.HTTPConnection")
	def test_html_response_explains_wrong_endpoint_without_reading_page(self, connection):
		response = Mock(status=200)
		response.getheader.return_value = "text/html"
		connection.return_value.getresponse.return_value = response
		with self.assertRaisesRegex(RuntimeError, "página HTML.* /capture"):
			CameraHTTP("http://camera/capture").read()
		response.read.assert_not_called()

	@patch("gestos.espcam.http.client.HTTPConnection")
	def test_error_body_timeout_preserves_http_error(self, connection):
		response = Mock(status=503)
		response.getheader.return_value = "text/plain"
		response.read.side_effect = TimeoutError()
		connection.return_value.getresponse.return_value = response
		with self.assertRaisesRegex(RuntimeError, "HTTP 503"):
			CameraHTTP("http://camera/capture").read()

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


class CameraWorkerTests(unittest.TestCase):
	def test_slow_frame_keeps_preview_and_original_timestamp_then_recovers(self):
		frame = np.full((240, 320, 3), 100, np.uint8)
		worker = ESPCameraWorker("http://camera/capture")
		failures, frames = [], []
		worker.failed.connect(failures.append)
		with patch("gestos.espcam.ensure_depth_model"), \
			patch("gestos.espcam.DepthEstimator"), \
			patch("gestos.espcam.DepthNavigator") as navigator, \
			patch("gestos.espcam.CameraHTTP") as camera, \
			patch("gestos.espcam.monotonic", return_value=10.), \
			patch.object(worker, "isInterruptionRequested", side_effect=[False, False, False, True]), \
			patch.object(worker, "msleep", side_effect=lambda _: frames.append(worker.take_frame())):
			camera.return_value.read.side_effect = [(frame, 9.), (frame, 10.)]
			navigator.return_value.analyze.return_value = (frame, frame, Navigation("FRENTE", "Livre", True))
			worker.run()
			camera.return_value.close.assert_called_once()
		self.assertEqual(failures, [])
		self.assertEqual([result[3] for result in frames], [9., 10.])
		self.assertFalse(frames[0][0].isNull())


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

	def test_stale_video_stops_and_resumes_on_fresh_result(self):
		self.state.response()
		self.feed()
		self.panel.set_active(True)
		self.feed()
		self.now += .5
		self.panel.refresh()
		self.assertTrue(self.panel.active)
		self.assertEqual(self.state.response(), b"FUSCA/1 PARAR\n")
		self.assertEqual(self.state.mode, "AUTO")
		self.feed("DIREITA")
		self.assertTrue(self.panel.active)
		self.assertEqual(self.state.response(), b"FUSCA/1 DIREITA\n")

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

	def test_delayed_frame_waits_with_preview_connected(self):
		self.state.response()
		self.feed()
		self.panel.set_active(True)
		worker = self.panel.worker
		with patch.object(self.panel.video, "set_frame") as show, patch.object(self.panel.video, "clear") as clear:
			self.feed(captured=self.now - .5)
			show.assert_called_once()
			clear.assert_not_called()
		self.assertIs(self.panel.worker, worker)
		self.assertFalse(worker.interrupted)
		self.assertTrue(self.panel.active)
		self.assertFalse(self.panel.start_button.isEnabled())
		self.assertEqual(self.state.response(), b"FUSCA/1 PARAR\n")
		self.feed()
		self.assertTrue(self.panel.active)
		self.assertEqual(self.state.response(), b"FUSCA/1 FRENTE\n")

	def test_manual_stop_while_waiting_prevents_automatic_resume(self):
		self.state.response()
		self.feed()
		self.panel.set_active(True)
		self.now += .5
		self.panel.refresh()
		self.panel.emergency_stop()
		self.feed()
		self.assertFalse(self.panel.active)
		self.assertEqual(self.state.response(), b"FUSCA/1 PARAR\n")

	def test_invalid_analysis_does_not_resume_waiting_robot(self):
		self.state.response()
		self.feed()
		self.panel.set_active(True)
		self.feed(captured=self.now - .5)
		self.panel.worker.frame = (self.image, self.image, Navigation("FRENTE", "Piso incerto", False), self.now)
		self.panel.refresh()
		self.assertTrue(self.panel.active)
		self.assertEqual(self.state.response(), b"FUSCA/1 PARAR\n")

	def test_robot_disconnect_still_requires_manual_restart(self):
		self.state.response()
		self.feed()
		self.panel.set_active(True)
		self.now += 2
		self.panel.refresh()
		self.assertFalse(self.panel.active)
		self.state.response()
		self.feed()
		self.assertFalse(self.panel.active)
		self.assertEqual(self.state.response(), b"FUSCA/1 PARAR\n")
