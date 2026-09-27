"""Protocol, freshness and DNS-SD lifecycle without robot hardware."""
import io
import unittest
from unittest.mock import Mock, patch

from gestos.network import CommandHandler, CommandState, RobotServer, SERVICE_TYPE


class CommandTests(unittest.TestCase):
	def setUp(self):
		self.now = 10.0
		self.state = CommandState(clock=lambda: self.now)

	def test_startup_stale_and_recovery(self):
		self.assertEqual(self.state.response(), b"FUSCA/1 PARAR\n")
		self.state.update("FRENTE")
		self.assertEqual(self.state.response(), b"FUSCA/1 FRENTE\n")
		self.now += 0.41
		self.assertEqual(self.state.response(), b"FUSCA/1 PARAR\n")
		self.state.update("RE")
		self.assertEqual(self.state.response(), b"FUSCA/1 RE\n")

	def test_only_known_manual_commands_move(self):
		for command in ("FRENTE", "RE", "ESQUERDA", "DIREITA", "PARAR"):
			self.state.update(command)
			self.assertEqual(self.state.response(), f"FUSCA/1 {command}\n".encode())
		for command, mode in (("FRENTE", "AUTO"), ("NENHUMA_MAO", "GESTOS"),
			("AGUARDANDO", "GESTOS"), ("TROCAR_MODO", "GESTOS"), ("BAD\nFRENTE", "GESTOS")):
			self.state.update(command, mode)
			self.assertEqual(self.state.response(), b"FUSCA/1 PARAR\n")

	def test_autonomous_commands_require_selected_mode_and_fresh_capture(self):
		self.state.update_autonomous("FRENTE", self.now)
		self.assertEqual(self.state.response(), b"FUSCA/1 PARAR\n")
		self.state.select_mode("AUTO")
		self.state.update_autonomous("ESQUERDA", self.now - .2)
		self.assertEqual(self.state.response(), b"FUSCA/1 ESQUERDA\n")
		self.now += .21
		self.assertEqual(self.state.response(), b"FUSCA/1 PARAR\n")
		for stamp in (self.now - 1, self.now + 1):
			self.state.update_autonomous("FRENTE", stamp)
			self.assertEqual(self.state.response(), b"FUSCA/1 PARAR\n")
		self.state.update_autonomous("FRENTE", self.now)
		self.state.select_mode("GESTOS")
		self.assertEqual(self.state.response(), b"FUSCA/1 PARAR\n")

	def test_connection_status_expires(self):
		self.assertFalse(self.state.connected())
		self.state.response()
		self.assertTrue(self.state.connected())
		self.now += 1.6
		self.assertFalse(self.state.connected())

	def test_protocol_rejects_invalid_and_oversized_requests(self):
		for data, replies in ((b"FUSCA/1 GET\n" * 2, 2), (b"GET\n", 0), (b"x" * 100, 0)):
			handler = object.__new__(CommandHandler)
			handler.connection = Mock()
			handler.server = Mock(state=self.state)
			handler.rfile = io.BytesIO(data)
			handler.wfile = io.BytesIO()
			handler.handle()
			self.assertEqual(handler.wfile.getvalue(), b"FUSCA/1 PARAR\n" * replies)


class ServerTests(unittest.TestCase):
	@patch("gestos.network.TCPServer")
	@patch("zeroconf.Zeroconf")
	@patch("ifaddr.get_adapters")
	def test_service_advertises_lan_address_and_bound_port(self, adapters, zeroconf, tcp):
		adapters.return_value = [Mock(ips=[Mock(ip="127.0.0.1"), Mock(ip="192.168.1.22"), Mock(ip=("::1", 0, 0))])]
		tcp.return_value.server_address = ("0.0.0.0", 8765)
		server = RobotServer()
		server.start()
		info = zeroconf.return_value.register_service.call_args.args[0]
		self.assertEqual(info.type, SERVICE_TYPE)
		self.assertEqual(info.parsed_addresses(), ["192.168.1.22"])
		self.assertEqual(info.port, 8765)
		server.state.update("FRENTE")
		server.close()
		server.close()
		self.assertEqual(server.state.response(), b"FUSCA/1 PARAR\n")
		tcp.return_value.shutdown.assert_called_once()
		zeroconf.return_value.close.assert_called_once()

	@patch("gestos.network.TCPServer")
	@patch("zeroconf.Zeroconf")
	@patch("ifaddr.get_adapters")
	def test_registration_failure_releases_socket(self, adapters, zeroconf, tcp):
		adapters.return_value = [Mock(ips=[Mock(ip="192.168.1.22")])]
		tcp.return_value.server_address = ("0.0.0.0", 8765)
		zeroconf.return_value.register_service.side_effect = OSError("mDNS unavailable")
		with self.assertRaises(OSError):
			RobotServer().start()
		tcp.return_value.server_close.assert_called_once()
		tcp.return_value.shutdown.assert_not_called()
		zeroconf.return_value.close.assert_called_once()
