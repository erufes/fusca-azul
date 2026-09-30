#pragma once
#include <Arduino.h>
#include "StateLog.h"

class Gy80 {
public:
	void begin(uint8_t sda, uint8_t scl);
	bool update(bool moving = false); // True only for a new calibrated sample.
	bool ready() const { return calibrated_ && !failed_ && millis() - lastSample_ <= 100; }
	float yawRate() const { return rate_; }
	float sampleSeconds() const { return dt_; }
private:
	bool read(uint8_t reg, uint8_t* data, uint8_t size);
	bool write(uint8_t reg, uint8_t value);
	void fail(const char* reason);
	StateLog state_{"GY80"};
	uint8_t address_ = 0;
	bool calibrated_ = false, failed_ = false;
	uint16_t samples_ = 0;
	uint32_t started_ = 0, lastPoll_ = 0, lastSample_ = 0;
	float sum_ = 0, bias_ = 0, rate_ = 0, dt_ = 0;
	float minimum_[3]{}, maximum_[3]{};
};
