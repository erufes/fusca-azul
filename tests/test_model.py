import io
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from gestos.model import ensure_model, model_path


class ModelTests(unittest.TestCase):
	def test_existing_model_never_uses_network(self):
		with TemporaryDirectory() as directory:
			path = Path(directory) / "model.task"
			path.write_bytes(b"existing")
			with patch("gestos.model.urlopen") as download:
				self.assertEqual(ensure_model(path, lambda _: None, lambda: False), path)
				download.assert_not_called()

	@patch.dict(os.environ, {}, clear=True)
	def test_successful_download_is_cached(self):
		with TemporaryDirectory() as directory:
			path = Path(directory) / "cache/model.task"
			with patch("gestos.model.urlopen", return_value=io.BytesIO(b"model")):
				ensure_model(path, lambda _: None, lambda: False)
			self.assertEqual(path.read_bytes(), b"model")
			self.assertEqual(list(path.parent.iterdir()), [path])

	@patch.dict(os.environ, {}, clear=True)
	def test_cancelled_download_does_not_leave_partial_model(self):
		with TemporaryDirectory() as directory:
			path = Path(directory) / "model.task"
			with patch("gestos.model.urlopen", return_value=io.BytesIO(b"partial")):
				with self.assertRaises(InterruptedError):
					ensure_model(path, lambda _: None, Mock(side_effect=[False, False, True, True]))
			self.assertEqual(list(path.parent.iterdir()), [])

	@patch.dict(os.environ, {}, clear=True)
	def test_failed_download_can_be_retried(self):
		with TemporaryDirectory() as directory:
			path = Path(directory) / "model.task"
			response = io.BytesIO()
			with patch("gestos.model.urlopen", return_value=response):
				with self.assertRaises(OSError):
					ensure_model(path, lambda _: None, lambda: False)
			self.assertFalse(path.exists())
			self.assertEqual(list(path.parent.iterdir()), [])

	def test_explicit_missing_model_is_not_downloaded(self):
		with TemporaryDirectory() as directory:
			path = Path(directory) / "missing.task"
			with patch.dict(os.environ, {"FUSCA_MODEL": str(path)}):
				self.assertEqual(model_path(), path)
				with patch("gestos.model.urlopen") as download:
					with self.assertRaises(FileNotFoundError):
						ensure_model(path, lambda _: None, lambda: False)
					download.assert_not_called()
