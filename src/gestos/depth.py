"""MiDaS v2.1 small ONNX inference on the computer (OpenCV DNN)."""
import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

import cv2
import numpy as np

MODEL_URL = "https://github.com/isl-org/MiDaS/releases/download/v2_1/model-small.onnx"


def depth_model_path():
	if override := os.environ.get("FUSCA_DEPTH_MODEL"):
		return Path(override).expanduser()
	if sys.platform == "win32":
		cache = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
	elif sys.platform == "darwin":
		cache = Path.home() / "Library/Caches"
	else:
		cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
	return cache / "fusca-azul" / "midas-v21-small.onnx"


def ensure_depth_model(path, status, cancelled):
	if cancelled():
		raise InterruptedError()
	if path.is_file() and path.stat().st_size:
		return path
	if os.environ.get("FUSCA_DEPTH_MODEL"):
		raise FileNotFoundError("O modelo indicado por FUSCA_DEPTH_MODEL não existe.")
	status("Baixando modelo de profundidade MiDaS na primeira conexão…")
	path.parent.mkdir(parents=True, exist_ok=True)
	temporary = None
	try:
		with urlopen(MODEL_URL, timeout=5) as response, NamedTemporaryFile(dir=path.parent, suffix=".download", delete=False) as output:
			temporary = Path(output.name)
			size = 0
			while True:
				if cancelled():
					raise InterruptedError()
				chunk = response.read(64 * 1024)
				if not chunk:
					break
				size += len(chunk)
				if size > 100_000_000:
					raise ValueError("Modelo de profundidade maior que o esperado")
				output.write(chunk)
		if cancelled():
			raise InterruptedError()
		# Parse before promoting the download, so truncated/corrupt files aren't cached.
		cv2.dnn.readNetFromONNX(str(temporary))
		temporary.replace(path)
		return path
	finally:
		if temporary is not None:
			temporary.unlink(missing_ok=True)


class DepthEstimator:
	def __init__(self, path):
		self.net = cv2.dnn.readNetFromONNX(str(path))
		self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
		self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

	def predict(self, frame):
		# Official v2.1 ONNX export includes mean/std normalization in the graph.
		rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).astype(np.float32) / 255
		rgb = cv2.resize(rgb, (256, 256), interpolation=cv2.INTER_CUBIC)
		self.net.setInput(np.ascontiguousarray(rgb.transpose(2, 0, 1)[None]))
		depth = self.net.forward().squeeze()
		if depth.shape != (256, 256) or not np.isfinite(depth).all():
			raise ValueError("Saída inválida do modelo de profundidade")
		return cv2.resize(depth, (320, 240), interpolation=cv2.INTER_CUBIC)
