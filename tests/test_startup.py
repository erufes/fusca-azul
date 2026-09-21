import contextlib
import io
import unittest
from unittest.mock import patch

import cv2
import numpy as np

import gestos


class StartupTests(unittest.TestCase):
    @patch.dict("os.environ", {}, clear=True)
    @patch("gestos.socket.socket")
    def test_network_address(self, socket):
        socket.return_value.__enter__.return_value.getsockname.return_value = (
            "192.168.1.42", 12345
        )
        self.assertEqual(gestos.page_url(), "http://192.168.1.42:8080/")

    @patch.dict("os.environ", {}, clear=True)
    @patch("gestos.socket.socket", side_effect=OSError)
    def test_offline_fallback(self, socket):
        url = gestos.page_url()
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            gestos.print_page_qr(url)
        self.assertEqual(url, "http://127.0.0.1:8080/")
        self.assertIn("só abre neste computador", output.getvalue())

    @patch.dict("os.environ", {"FUSCA_URL": "https://fusca.example/"})
    @patch("gestos.socket.socket")
    def test_explicit_url(self, socket):
        self.assertEqual(gestos.page_url(), "https://fusca.example/")
        socket.assert_not_called()

    def test_printed_qr_decodes_to_page_url(self):
        url = "http://192.168.1.42:8080/"
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            gestos.print_page_qr(url)
        # Reconstruct the actual terminal half-block output as pixels.
        rows = [line for line in output.getvalue().splitlines()
                if line and set(line) <= set("\u00a0▀▄█")]
        pixels = []
        halves = {"\u00a0": (0, 0), "▀": (255, 0),
                  "▄": (0, 255), "█": (255, 255)}
        for row in rows:
            pixels.extend([[halves[c][i] for c in row] for i in (0, 1)])
        image = np.repeat(np.repeat(np.array(pixels, dtype=np.uint8), 8, 0), 8, 1)
        decoded, _, _ = cv2.QRCodeDetector().detectAndDecode(image)
        self.assertEqual(decoded, url)

    @patch("gestos.uvicorn.run")
    @patch("gestos.print_page_qr")
    @patch("gestos.page_url", return_value="http://192.168.1.42:8080/")
    def test_cli_prints_qr_and_starts_server_on_matching_port(self, url, print_qr, run):
        gestos.main()
        print_qr.assert_called_once_with(url.return_value)
        self.assertEqual(run.call_args.kwargs["port"], 8080)


if __name__ == "__main__":
    unittest.main()
