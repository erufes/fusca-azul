"""Host simulation of gyro failures, calibration and differential motor control."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class FirmwareTests(unittest.TestCase):
	@unittest.skipUnless(shutil.which("g++"), "g++ is required for firmware simulation")
	def test_stability_and_motor_interlocks(self):
		root = Path(__file__).resolve().parents[1]
		firmware = root / "src/firmware"
		with tempfile.TemporaryDirectory() as folder:
			binary = str(Path(folder) / "stability")
			subprocess.run([
				"g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
				"-I" + str(root / "tests/firmware/fakes"), "-I" + str(firmware),
				str(root / "tests/firmware/stability.cpp"),
				*[str(firmware / name) for name in ("Gy80.cpp", "Motor.cpp", "Robot.cpp")],
				"-o", binary,
			], check=True, capture_output=True, text=True)
			subprocess.run([binary], check=True, capture_output=True, text=True)
