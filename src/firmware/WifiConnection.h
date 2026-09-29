#pragma once
#include <Arduino.h>

namespace WifiConnection {
	void begin();
	void update();
	bool connected();
	const String& hostname();
}
