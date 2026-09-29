#include "WifiCredentials.h"
#include <LittleFS.h>

namespace {
constexpr char CONFIG_PATH[] = "/wifi.bin";
}

bool WifiCredentials::valid() const {
	return magic == 0x46555331 && ssid[0] &&
		memchr(ssid, 0, sizeof(ssid)) && memchr(password, 0, sizeof(password));
}

bool CredentialStore::begin(WifiCredentials& saved) {
	if (!LittleFS.begin()) return false;
	File file = LittleFS.open(CONFIG_PATH, "r");
	if (file && file.size() == sizeof(saved)) file.read(reinterpret_cast<uint8_t*>(&saved), sizeof(saved));
	file.close();
	return true;
}

bool CredentialStore::save(const WifiCredentials& candidate) {
	File file = LittleFS.open("/wifi.tmp", "w");
	if (!file) return false;
	bool written = file.write(reinterpret_cast<const uint8_t*>(&candidate), sizeof(candidate)) == sizeof(candidate);
	file.close();
	return written && LittleFS.rename("/wifi.tmp", CONFIG_PATH);
}
