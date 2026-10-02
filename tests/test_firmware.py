"""Host simulation of full-duty motor control and command timeout."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class FirmwareTests(unittest.TestCase):
	@unittest.skipUnless(shutil.which("g++"), "g++ is required for firmware simulation")
	def test_motor_commands_and_timeout(self):
		root = Path(__file__).resolve().parents[1]
		firmware = root / "src/firmware"
		with tempfile.TemporaryDirectory() as folder:
			binary = str(Path(folder) / "motors")
			subprocess.run([
				"g++", "-std=c++17", "-Wall", "-Wextra", "-Werror",
				"-I" + str(root / "tests/firmware/fakes"), "-I" + str(firmware),
				str(root / "tests/firmware/motors.cpp"),
				*[str(firmware / name) for name in ("Motor.cpp", "Robot.cpp")],
				"-o", binary,
			], check=True, capture_output=True, text=True)
			subprocess.run([binary], check=True, capture_output=True, text=True)
