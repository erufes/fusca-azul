"""Local robot command server, advertised through DNS-SD."""
import logging
import socket
import socketserver
import threading
from time import monotonic
from uuid import uuid4


SERVICE_TYPE = "_fusca-azul._tcp.local."
COMMANDS = frozenset({"FRENTE", "RE", "ESQUERDA", "DIREITA", "PARAR"})
logger = logging.getLogger(__name__)


class CommandState:
	"""Only recent recognition results can authorize movement."""
	def __init__(self, clock=monotonic):
		self.clock = clock
		self.lock = threading.Lock()
		self.command = "PARAR"
		self.updated = float("-inf")
		self.last_robot = float("-inf")

	def update(self, command, mode="GESTOS"):
		with self.lock:
			self.command = command if mode == "GESTOS" and command in COMMANDS else "PARAR"
			self.updated = self.clock()

	def response(self):
		with self.lock:
			now = self.clock()
			self.last_robot = now
			command = self.command if now - self.updated <= 0.4 else "PARAR"
			return f"FUSCA/1 {command}\n".encode("ascii")

	def connected(self):
		with self.lock:
			return self.clock() - self.last_robot < 1.5


class CommandHandler(socketserver.StreamRequestHandler):
	def handle(self):
		self.connection.settimeout(2)
		try:
			while self.rfile.readline(65) == b"FUSCA/1 GET\n":
				self.wfile.write(self.server.state.response())
		except (OSError, TimeoutError):
			pass


class TCPServer(socketserver.ThreadingTCPServer):
	allow_reuse_address = True
	daemon_threads = True


class RobotServer:
	def __init__(self, state=None, port=8765):
		self.state = state if state is not None else CommandState()
		self.port = port
		self.server = None
		self.zeroconf = None
		self.info = None
		self.thread = None

	def start(self):
		try:
			import ifaddr
			from zeroconf import IPVersion, ServiceInfo, Zeroconf

			addresses = sorted({ip.ip for adapter in ifaddr.get_adapters() for ip in adapter.ips
				if isinstance(ip.ip, str) and not ip.ip.startswith("127.") and ip.ip != "0.0.0.0"})
			if not addresses:
				raise OSError("Nenhuma interface IPv4 disponível. Conecte o computador à rede e reabra o aplicativo.")
			self.server = TCPServer(("0.0.0.0", self.port), CommandHandler)
			self.server.state = self.state
			identity = "fusca-servidor-" + uuid4().hex[:8]
			self.info = ServiceInfo(SERVICE_TYPE, f"{identity}.{SERVICE_TYPE}",
				addresses=[socket.inet_aton(ip) for ip in addresses],
				port=self.server.server_address[1], properties={"version": "1"}, server=f"{identity}.local.")
			self.zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
			self.zeroconf.register_service(self.info)
			self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.1}, daemon=True)
			self.thread.start()
			logger.info("Servidor do robô disponível na porta %s", self.server.server_address[1])
		except Exception:
			self.close()
			raise

	def close(self):
		self.state.update("PARAR")
		if self.server is not None:
			if self.thread is not None:
				self.server.shutdown()
				self.thread.join()
			self.server.server_close()
			self.server = None
			self.thread = None
		if self.zeroconf is not None:
			self.zeroconf.close()
			self.zeroconf = None
