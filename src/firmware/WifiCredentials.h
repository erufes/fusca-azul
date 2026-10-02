#pragma once
#include <Arduino.h>

struct WifiCredentials {
	uint32_t magic;
	char ssid[33];
	char password[65];
	bool valid() const;
};

namespace CredentialStore {
	bool begin(WifiCredentials& saved);
	bool save(const WifiCredentials& candidate);
}
