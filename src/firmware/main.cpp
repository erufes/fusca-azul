#include <Arduino.h>
#include <DNSServer.h>
#include <ESP8266WebServer.h>
#include <ESP8266WiFi.h>
#include <ESP8266mDNS.h>
#include <LittleFS.h>

#include "Robot.h"

namespace {
constexpr uint32_t WIFI_TIMEOUT = 20000;
constexpr uint32_t REPLY_TIMEOUT = 400;
constexpr char CONFIG_PATH[] = "/wifi.bin";
Motor leftMotor(D0, D2, D1);  // ENA, IN1, IN2
Motor rightMotor(D5, D3, D4); // ENB, IN3, IN4
Robot robot(leftMotor, rightMotor);
ESP8266WebServer portal(80);
DNSServer dns;
WiFiClient server;
struct Credentials {
	uint32_t magic;
	char ssid[33];
	char password[65];
};
Credentials saved{}, candidate{};
bool storageReady = false, portalOpen = false, testing = false, joining = false;
bool online = false, mdnsReady = false, pending = false, restarting = false;
uint32_t joinStarted = 0, lastDiscovery = 0, requested = 0, lastPoll = 0, restartAt = 0;
String hostname, response, message = "Informe uma rede Wi-Fi de 2,4 GHz.";

bool valid(const Credentials& value) {
	return value.magic == 0x46555331 && value.ssid[0] &&
		memchr(value.ssid, 0, sizeof(value.ssid)) && memchr(value.password, 0, sizeof(value.password));
}

bool saveCredentials() {
	File file = LittleFS.open("/wifi.tmp", "w");
	if (!file) return false;
	bool written = file.write(reinterpret_cast<const uint8_t*>(&candidate), sizeof(candidate)) == sizeof(candidate);
	file.close();
	// LittleFS rename atomically replaces the old configuration after a complete write.
	return written && LittleFS.rename("/wifi.tmp", CONFIG_PATH);
}

void disconnectServer() {
	robot.stop();
	server.stop();
	pending = false;
	response = "";
}

void join(const Credentials& credentials) {
	WiFi.disconnect();
	WiFi.begin(credentials.ssid, credentials.password);
	joining = true;
	joinStarted = millis();
}

void page() {
	String html = F("<!doctype html><html lang='pt-BR'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Fusca Azul</title><style>body{font:18px sans-serif;background:#182031;color:#e7edf7;max-width:440px;margin:40px auto;padding:20px}input,button{box-sizing:border-box;width:100%;padding:12px;margin:8px 0}button{background:#bcd6f6;border:0;border-radius:8px}</style><h1>Conectar o Fusca Azul</h1><p>");
	html += message;
	html += F("</p><form method='post' action='/wifi'><label>Nome da rede (SSID)<input name='ssid' maxlength='32' required autocomplete='off'></label><label>Senha<input name='password' type='password' maxlength='64' autocomplete='new-password'></label><button>Conectar e salvar</button></form><p>Deixe a senha vazia apenas para redes abertas. Após conectar, o robô salva a rede e reinicia.</p><a style='color:#bcd6f6' href='/'>Atualizar situação</a></html>");
	portal.sendHeader("Cache-Control", "no-store");
	portal.send(200, "text/html; charset=utf-8", html);
}

void openPortal() {
	disconnectServer();
	WiFi.mode(WIFI_AP_STA);
	String apName = "Fusca-Azul-" + String(ESP.getChipId(), HEX);
	// Local provisioning only; the AP is removed once credentials are validated.
	WiFi.softAP(apName.c_str());
	dns.start(53, "*", WiFi.softAPIP());
	portal.on("/", HTTP_GET, page);
	portal.on("/wifi", HTTP_POST, []() {
		if (testing || restarting) {
			portal.send(409, "text/plain; charset=utf-8", "Conexão em andamento. Aguarde e atualize a página.");
			return;
		}
		String ssid = portal.arg("ssid"), password = portal.arg("password");
		bool passwordValid = password.isEmpty() || (password.length() >= 8 && password.length() <= 63);
		if (password.length() == 64) {
			passwordValid = true;
			for (unsigned i = 0; i < password.length(); ++i) if (!isxdigit(password[i])) passwordValid = false;
		}
		if (ssid.isEmpty() || ssid.length() > 32 || !passwordValid || strlen(ssid.c_str()) != ssid.length() || strlen(password.c_str()) != password.length()) {
			portal.send(400, "text/plain; charset=utf-8", "Nome ou senha inválidos. Use até 32 bytes no nome e 8–63 caracteres na senha (ou 64 dígitos hexadecimais).");
			return;
		}
		if (!storageReady) {
			portal.send(503, "text/plain; charset=utf-8", "Não foi possível abrir a memória de configuração. Verifique o monitor serial.");
			return;
		}
		candidate = {};
		candidate.magic = 0x46555331;
		ssid.toCharArray(candidate.ssid, sizeof(candidate.ssid));
		password.toCharArray(candidate.password, sizeof(candidate.password));
		message = "Testando a conexão. Aguarde até 20 segundos e atualize a página. Se conectar, o hotspot será encerrado.";
		page();
		testing = true;
		join(candidate);
	});
	portal.onNotFound([]() {
		portal.sendHeader("Location", "http://192.168.4.1/", true);
		portal.send(302, "text/plain", "");
	});
	portal.begin();
	portalOpen = true;
	Serial.printf("[WIFI] Configure na rede %s em http://192.168.4.1\n", apName.c_str());
}

void wifiLoop() {
	if (portalOpen) {
		dns.processNextRequest();
		portal.handleClient();
	}
	if (restarting) {
		if (millis() - restartAt >= 1500) ESP.restart();
		return;
	}
	if (joining && WiFi.status() == WL_CONNECTED) {
		joining = false;
		if (testing) {
			testing = false;
			if (!saveCredentials()) {
				message = "Falha ao salvar. A rede anterior foi preservada. Tente novamente.";
				WiFi.disconnect();
				return;
			}
			message = "Rede conectada e salva. Reiniciando…";
			restarting = true;
			restartAt = millis();
			return;
		}
		online = true;
		if (portalOpen) {
			portal.stop();
			dns.stop();
			WiFi.softAPdisconnect(true);
			WiFi.mode(WIFI_STA);
			portalOpen = false;
		}
		mdnsReady = MDNS.begin(hostname.c_str());
		lastDiscovery = millis() - 5000;
		Serial.printf("[WIFI] Conectado: %s\n", WiFi.localIP().toString().c_str());
	}
	if (joining && millis() - joinStarted >= WIFI_TIMEOUT) {
		joining = false;
		testing = false;
		WiFi.disconnect();
		message = "Não foi possível conectar. Confira o nome e a senha. A última rede salva foi mantida.";
		if (!portalOpen) openPortal();
	}
	if (online && WiFi.status() != WL_CONNECTED) {
		online = false;
		disconnectServer();
		MDNS.close();
		mdnsReady = false;
		join(saved);
	}
	// Continue trying the last successful network while the portal is idle.
	if (portalOpen && !joining && valid(saved) && millis() - joinStarted >= 30000) join(saved);
}

bool apply(const String& line) {
	if (line == "FUSCA/1 FRENTE") robot.forward();
	else if (line == "FUSCA/1 RE") robot.backward();
	else if (line == "FUSCA/1 ESQUERDA") robot.left();
	else if (line == "FUSCA/1 DIREITA") robot.right();
	else if (line == "FUSCA/1 PARAR") robot.stop();
	else return false;
	return true;
}

void commandLoop() {
	if (!online) return;
	if (mdnsReady) MDNS.update();
	if (!server.connected()) {
		disconnectServer();
		if (millis() - lastDiscovery < 5000) return;
		lastDiscovery = millis();
		if (!mdnsReady) mdnsReady = MDNS.begin(hostname.c_str());
		if (!mdnsReady) return;
		int count = MDNS.queryService("fusca-azul", "tcp");
		// Ambiguous servers must not compete for control of this robot.
		if (count != 1) return;
		server.setTimeout(100);
		if (server.connect(MDNS.IP(0), MDNS.port(0))) {
			server.setNoDelay(true);
			lastPoll = millis() - 100;
			Serial.println("[SERVIDOR] Conectado");
		}
		return;
	}
	if (pending && millis() - requested >= REPLY_TIMEOUT) {
		disconnectServer();
		return;
	}
	while (server.available()) {
		char c = server.read();
		if (!pending || response.length() >= 32) {
			disconnectServer();
			return;
		}
		if (c == '\n') {
			if (!apply(response)) {
				disconnectServer();
				return;
			}
			pending = false;
			response = "";
		} else response += c;
	}
	if (!pending && millis() - lastPoll >= 100) {
		requested = lastPoll = millis();
		pending = true;
		if (server.print("FUSCA/1 GET\n") != 12) disconnectServer();
	}
}
}

void setup() {
	robot.begin();
	Serial.begin(115200);
	WiFi.persistent(false); // Credentials are stored only after a successful connection.
	WiFi.mode(WIFI_STA);
	WiFi.setAutoReconnect(false);
	hostname = "fusca-azul-" + String(ESP.getChipId(), HEX);
	WiFi.hostname(hostname);
	storageReady = LittleFS.begin();
	if (storageReady) {
		File file = LittleFS.open(CONFIG_PATH, "r");
		if (file && file.size() == sizeof(saved)) file.read(reinterpret_cast<uint8_t*>(&saved), sizeof(saved));
		file.close();
	} else Serial.println("[WIFI] Falha ao montar LittleFS");
	if (valid(saved)) join(saved);
	else openPortal();
}

void loop() {
	wifiLoop();
	commandLoop();
	delay(1);
}
