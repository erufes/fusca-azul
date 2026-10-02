"""Protocol, freshness and DNS-SD lifecycle without robot hardware."""
import io
import unittest
from unittest.mock import Mock, patch

from gestos.network import CommandHandler, CommandState, RobotServer, SERVICE_TYPE, discovery_address


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
			handler.client_address = ("192.168.1.50", 12345)
			handler.server = Mock(state=self.state)
			handler.rfile = io.BytesIO(data)
			handler.wfile = io.BytesIO()
			handler.handle()
			self.assertEqual(handler.wfile.getvalue(), b"FUSCA/1 PARAR\n" * replies)


class ServerTests(unittest.TestCase):
	@patch("gestos.network.socket.socket")
	def test_discovery_uses_multicast_route_without_sending_data(self, socket_factory):
		probe = socket_factory.return_value.__enter__.return_value
		probe.getsockname.return_value = ("192.168.1.22", 54321)
		self.assertEqual(discovery_address(), "192.168.1.22")
		probe.connect.assert_called_once_with(("224.0.0.251", 5353))
		probe.send.assert_not_called()
		probe.sendto.assert_not_called()

	@patch("gestos.network.socket.socket")
	def test_discovery_rejects_loopback(self, socket_factory):
		probe = socket_factory.return_value.__enter__.return_value
		probe.getsockname.return_value = ("127.0.0.1", 54321)
		with self.assertRaises(OSError):
			discovery_address()

	@patch("gestos.network.TCPServer")
	@patch("zeroconf.Zeroconf")
	@patch("gestos.network.discovery_address", return_value="192.168.1.22")
	def test_service_advertises_lan_address_and_bound_port(self, address, zeroconf, tcp):
		tcp.return_value.server_address = ("0.0.0.0", 8765)
		server = RobotServer()
		server.start()
		info = zeroconf.return_value.register_service.call_args.args[0]
		self.assertEqual(info.type, SERVICE_TYPE)
		self.assertEqual(info.parsed_addresses(), ["192.168.1.22"])
		self.assertEqual(info.port, 8765)
		self.assertEqual(zeroconf.call_args.kwargs["interfaces"], ["192.168.1.22"])
		server.state.update("FRENTE")
		server.close()
		server.close()
		self.assertEqual(server.state.response(), b"FUSCA/1 PARAR\n")
		tcp.return_value.shutdown.assert_called_once()
		zeroconf.return_value.close.assert_called_once()

	@patch("gestos.network.TCPServer")
	@patch("zeroconf.Zeroconf")
	@patch("gestos.network.discovery_address", return_value="192.168.1.22")
	def test_registration_failure_releases_socket(self, address, zeroconf, tcp):
		tcp.return_value.server_address = ("0.0.0.0", 8765)
		zeroconf.return_value.register_service.side_effect = OSError("mDNS unavailable")
		with self.assertRaises(OSError):
			RobotServer().start()
		tcp.return_value.server_close.assert_called_once()
		tcp.return_value.shutdown.assert_not_called()
		zeroconf.return_value.close.assert_called_once()
