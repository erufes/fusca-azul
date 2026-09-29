#include "WifiConnection.h"
#include "WifiCredentials.h"
#include "StateLog.h"
#include <DNSServer.h>
#include <ESP8266WebServer.h>
#include <ESP8266WiFi.h>

namespace {
constexpr uint32_t WIFI_TIMEOUT = 20000;
ESP8266WebServer portal(80);
DNSServer dns;
WifiCredentials saved{}, candidate{};
bool storageReady = false, portalOpen = false, testing = false, joining = false;
bool online = false, restarting = false;
uint32_t joinStarted = 0, restartAt = 0;
String deviceHostname, message = "Selecione uma rede Wi-Fi de 2,4 GHz.";
StateLog wifiState("WIFI"), portalState("PORTAL"), scanState("BUSCA_WIFI");
bool scanning = false;

void scan() {
	scanning = true;
	scanState.set("BUSCANDO");
	WiFi.scanNetworks(true);
}

void join(const WifiCredentials& credentials) {
	WiFi.disconnect();
	WiFi.begin(credentials.ssid, credentials.password);
	joining = true;
	wifiState.set(testing ? "TESTANDO_REDE" : "CONECTANDO");
	joinStarted = millis();
}

String escapeHtml(String value) {
	value.replace("&", "&amp;");
	value.replace("<", "&lt;");
	value.replace(">", "&gt;");
	value.replace("\"", "&quot;");
	value.replace("'", "&#39;");
	return value;
}

void page() {
	int count = WiFi.scanComplete();
	bool busy = joining || testing || restarting;
	String html = F("<!doctype html><html lang='pt-BR'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Fusca Azul</title><style>body{font:18px sans-serif;background:#182031;color:#e7edf7;max-width:440px;margin:40px auto;padding:20px}input,select,button{box-sizing:border-box;width:100%;padding:12px;margin:8px 0}button{background:#bcd6f6;border:0;border-radius:8px}button:disabled{opacity:.5}</style><h1>Conectar o Fusca Azul</h1><p>");
	html += message;
	html += F("</p>");
	if (busy) {
		html += F("<p>Conexão em andamento. Aguarde e atualize a situação.</p>");
	} else if (count == WIFI_SCAN_RUNNING) {
		html += F("<p>Buscando redes próximas… A lista aparecerá automaticamente.</p>");
		portal.sendHeader("Refresh", "2; url=/");
	} else {
		String options;
		for (int i = 0; i < count; ++i) {
			String ssid = WiFi.SSID(i);
			if (ssid.isEmpty()) continue;
			bool duplicate = false;
			for (int j = 0; j < i; ++j) if (WiFi.SSID(j) == ssid) duplicate = true;
			if (duplicate) continue;
			String escaped = escapeHtml(ssid);
			options += "<option value='" + escaped + "'>" + escaped + "</option>";
		}
		if (!options.isEmpty()) {
			html += F("<form method='post' action='/wifi'><label>Rede Wi-Fi<select name='ssid' required><option value='' disabled selected>Selecione uma rede</option>");
			html += options;
			html += F("</select></label><label>Senha<input name='password' type='password' maxlength='64' autocomplete='new-password'></label><button>Conectar e salvar</button></form><p>Deixe a senha vazia apenas para redes abertas. Após conectar, o robô salva a rede e reinicia.</p>");
		} else if (count == WIFI_SCAN_FAILED) {
			html += F("<p>Não foi possível buscar as redes. Tente novamente.</p>");
		} else {
			html += F("<p>Nenhuma rede encontrada. Aproxime o robô do roteador e tente novamente.</p>");
		}
		html += F("<form method='post' action='/scan'><button>Buscar redes novamente</button></form><p>Aparecem apenas redes de 2,4 GHz com nome visível.</p>");
	}
	html += F("<a style='color:#bcd6f6' href='/'>Atualizar situação</a></html>");
	portal.sendHeader("Cache-Control", "no-store");
	portal.send(200, "text/html; charset=utf-8", html);
}

void openPortal() {
	WiFi.mode(WIFI_AP_STA);
	String apName = "Fusca-Azul-" + String(ESP.getChipId(), HEX);
	// Local provisioning only; the AP is removed once credentials are validated.
	WiFi.softAP(apName.c_str());
	dns.start(53, "*", WiFi.softAPIP());
	scan();
	portal.on("/", HTTP_GET, page);
	portal.on("/scan", HTTP_POST, []() {
		if (!joining && !testing && !restarting && WiFi.scanComplete() != WIFI_SCAN_RUNNING) {
			scan();
		}
		portal.sendHeader("Location", "/", true);
		portal.send(303, "text/plain", "");
	});
	portal.on("/wifi", HTTP_POST, []() {
		if (testing || restarting || WiFi.scanComplete() == WIFI_SCAN_RUNNING) {
			portal.send(409, "text/plain; charset=utf-8", "Conexão em andamento. Aguarde e atualize a página.");
			return;
		}
		String ssid = portal.arg("ssid"), password = portal.arg("password");
		bool found = false;
		for (int i = 0; i < WiFi.scanComplete(); ++i) if (WiFi.SSID(i) == ssid) found = true;
		if (!found) {
			portal.send(400, "text/plain; charset=utf-8", "Selecione uma rede da lista. Atualize a página e tente novamente.");
			return;
		}
		bool passwordValid = password.isEmpty() || (password.length() >= 8 && password.length() <= 63);
		if (password.length() == 64) {
			passwordValid = true;
			for (unsigned i = 0; i < password.length(); ++i) if (!isxdigit(password[i])) passwordValid = false;
		}
		if (ssid.isEmpty() || ssid.length() > 32 || !passwordValid || strlen(ssid.c_str()) != ssid.length() || strlen(password.c_str()) != password.length()) {
			portal.send(400, "text/plain; charset=utf-8", "Rede ou senha inválida. Selecione uma rede e use 8–63 caracteres na senha (ou 64 dígitos hexadecimais).");
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
		testing = true;
		page();
		join(candidate);
	});
	portal.onNotFound([]() {
		portal.sendHeader("Location", "http://192.168.4.1/", true);
		portal.send(302, "text/plain", "");
	});
	portal.begin();
	portalOpen = true;
	portalState.set("ABERTO");
	Serial.printf("[WIFI] Configure na rede %s em http://192.168.4.1\n", apName.c_str());
}

}

void WifiConnection::update() {
	if (scanning && WiFi.scanComplete() != WIFI_SCAN_RUNNING) {
		scanning = false;
		int count = WiFi.scanComplete();
		scanState.set(count < 0 ? "FALHOU" : "CONCLUIDA");
		if (count >= 0) Serial.printf("[BUSCA_WIFI] %d redes encontradas\n", count);
	}
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
			if (!CredentialStore::save(candidate)) {
				message = "Falha ao salvar. A rede anterior foi preservada. Tente novamente.";
				wifiState.set("FALHA_AO_SALVAR");
				WiFi.disconnect();
				return;
			}
			message = "Rede conectada e salva. Reiniciando…";
			wifiState.set("REINICIANDO", "Rede validada e salva");
			restarting = true;
			restartAt = millis();
			return;
		}
		online = true;
		wifiState.set("CONECTADO");
		if (portalOpen) {
			WiFi.scanDelete();
			portal.stop();
			dns.stop();
			WiFi.softAPdisconnect(true);
			WiFi.mode(WIFI_STA);
			portalOpen = false;
			portalState.set("FECHADO");
		}
		Serial.printf("[WIFI] Conectado: %s\n", WiFi.localIP().toString().c_str());
	}
	if (joining && millis() - joinStarted >= WIFI_TIMEOUT) {
		wifiState.set("TEMPO_ESGOTADO", "Sem conexao apos 20 segundos");
		joining = false;
		testing = false;
		WiFi.disconnect();
		message = "Não foi possível conectar. Confira a rede selecionada e a senha. A última rede salva foi mantida.";
		if (!portalOpen) openPortal();
	}
	if (online && WiFi.status() != WL_CONNECTED) {
		online = false;
		wifiState.set("DESCONECTADO", "Conexao Wi-Fi perdida");
		join(saved);
	}
	// Continue trying the last successful network while the portal is idle.
	if (portalOpen && !joining && WiFi.scanComplete() != WIFI_SCAN_RUNNING && saved.valid() && millis() - joinStarted >= 30000) join(saved);
}

bool WifiConnection::connected() { return online && WiFi.status() == WL_CONNECTED; }
const String& WifiConnection::hostname() { return deviceHostname; }

void WifiConnection::begin() {
	WiFi.persistent(false);
	WiFi.mode(WIFI_STA);
	WiFi.setAutoReconnect(false);
	deviceHostname = "fusca-azul-" + String(ESP.getChipId(), HEX);
	WiFi.hostname(deviceHostname);
	storageReady = CredentialStore::begin(saved);
	if (!storageReady) Serial.println("[WIFI] Falha ao montar LittleFS");
	if (saved.valid()) join(saved);
	else {
		wifiState.set("SEM_CONFIGURACAO");
		openPortal();
	}
}
