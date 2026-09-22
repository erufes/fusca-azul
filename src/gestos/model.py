"""Locate or download the hand model; no camera or UI dependencies."""
import os
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

MODEL_URL = (
	"https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
	"hand_landmarker/float16/1/hand_landmarker.task"
)


def model_path():
	if override := os.environ.get("FUSCA_MODEL"):
		return Path(override).expanduser()
	local = Path(__file__).parent / "model" / "hand_landmarker.task"
	if local.is_file():
		return local
	if sys.platform == "win32":
		cache = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
	elif sys.platform == "darwin":
		cache = Path.home() / "Library/Caches"
	else:
		cache = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
	return cache / "fusca-azul" / "hand_landmarker.task"


def ensure_model(path, status, cancelled):
	if cancelled():
		raise InterruptedError()
	if path.is_file() and path.stat().st_size:
		return path
	if os.environ.get("FUSCA_MODEL"):
		raise FileNotFoundError("O arquivo indicado por FUSCA_MODEL não foi encontrado.")
	status("Preparando reconhecimento: baixando o modelo pela primeira vez…")
	temporary = None
	try:
		path.parent.mkdir(parents=True, exist_ok=True)
		with urlopen(MODEL_URL, timeout=15) as response:
			with NamedTemporaryFile(dir=path.parent, suffix=".download", delete=False) as output:
				temporary = Path(output.name)
				while not cancelled():
					chunk = response.read(256 * 1024)
					if not chunk:
						break
					output.write(chunk)
				if cancelled():
					raise InterruptedError()
		if not temporary.stat().st_size:
			raise OSError("O download do modelo retornou um arquivo vazio.")
		temporary.replace(path)
		return path
	except InterruptedError:
		raise
	except OSError as error:
		raise OSError(
			"Não foi possível preparar o modelo. Verifique a conexão com a internet "
			"e a permissão para gravar no cache; depois tente novamente. "
			f"Detalhe: {error}"
		) from error
	finally:
		if temporary is not None:
			temporary.unlink(missing_ok=True)
