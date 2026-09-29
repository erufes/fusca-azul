#pragma once
#include <ESP8266WiFi.h>
#include "Robot.h"
#include "StateLog.h"

class GestosConnection {
public:
	explicit GestosConnection(Robot& robot) : robot(robot) {}
	void update(bool wifiConnected, const String& hostname);
private:
	bool apply(const String& line);
	void disconnect(const char* state, const char* reason = "");
	Robot& robot;
	WiFiClient server;
	StateLog state{"GESTOS"};
	bool networkReady = false, mdnsReady = false, pending = false, tcpConnected = false;
	uint32_t lastDiscovery = 0, requested = 0, lastPoll = 0;
	String response;
};
