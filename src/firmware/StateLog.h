#pragma once
#include <Arduino.h>

// Emit only transitions; repeated polling must not flood the serial port.
class StateLog {
public:
	explicit StateLog(const char* component) : component_(component) {}
	void set(const char* next, const char* reason = "") {
		if (strcmp(state_, next) == 0) return;
		Serial.printf("[%lu ms][%s] %s -> %s%s%s\n", millis(), component_, state_, next,
			reason[0] ? ": " : "", reason);
		state_ = next;
	}
private:
	const char* component_;
	const char* state_ = "INICIAL";
};
