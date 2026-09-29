#include "GestosConnection.h"
#include <ESP8266mDNS.h>

namespace {
constexpr uint32_t REPLY_TIMEOUT = 400;
}

void GestosConnection::disconnect(const char* next, const char* reason) {
	robot.stop();
	server.stop();
	tcpConnected = false;
	pending = false;
	response = "";
	state.set(next, reason);
}

bool GestosConnection::apply(const String& line) {
	if (line == "FUSCA/1 FRENTE") robot.forward();
	else if (line == "FUSCA/1 RE") robot.backward();
	else if (line == "FUSCA/1 ESQUERDA") robot.left();
	else if (line == "FUSCA/1 DIREITA") robot.right();
	else if (line == "FUSCA/1 PARAR") robot.stop();
	else return false;
	return true;
}

void GestosConnection::update(bool wifiConnected, const String& hostname) {
	if (!wifiConnected) {
		disconnect("AGUARDANDO_WIFI");
		if (mdnsReady) MDNS.close();
		mdnsReady = false;
		networkReady = false;
		return;
	}
	if (!networkReady) {
		networkReady = true;
		lastDiscovery = millis() - 5000;
		state.set("DESCOBRINDO");
	}
	if (mdnsReady) MDNS.update();
	if (!server.connected()) {
		if (tcpConnected) disconnect("DESCONECTADO", "Conexao TCP encerrada");
		if (millis() - lastDiscovery < 5000) return;
		lastDiscovery = millis();
		if (!mdnsReady) mdnsReady = MDNS.begin(hostname.c_str());
		if (!mdnsReady) { state.set("FALHA_MDNS"); return; }
		int count = MDNS.queryService("fusca-azul", "tcp");
		// Ambiguous servers must not compete for control of this robot.
		if (count != 1) {
			state.set(count == 0 ? "SERVIDOR_AUSENTE" : "MULTIPLOS_SERVIDORES");
			return;
		}
		server.setTimeout(100);
		Serial.printf("[GESTOS] Tentando %s:%u\n", MDNS.IP(0).toString().c_str(), MDNS.port(0));
		if (server.connect(MDNS.IP(0), MDNS.port(0))) {
			tcpConnected = true;
			server.setNoDelay(true);
			lastPoll = millis() - 100;
			state.set("CONECTADO");
		} else state.set("FALHA_TCP");
		return;
	}
	if (pending && millis() - requested >= REPLY_TIMEOUT) {
		disconnect("TEMPO_ESGOTADO", "Sem resposta do Gestos por 400 ms");
		return;
	}
	while (server.available()) {
		char c = server.read();
		if (!pending || response.length() >= 32) {
			disconnect("ERRO_PROTOCOLO", "Resposta inesperada ou longa demais");
			return;
		}
		if (c == '\n') {
			if (!apply(response)) {
				disconnect("ERRO_PROTOCOLO", "Comando invalido");
				return;
			}
			pending = false;
			response = "";
		} else response += c;
	}
	if (!pending && millis() - lastPoll >= 100) {
		requested = lastPoll = millis();
		pending = true;
		if (server.print("FUSCA/1 GET\n") != 12) disconnect("FALHA_ENVIO");
	}
}
