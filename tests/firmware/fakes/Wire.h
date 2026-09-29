#pragma once
#include "Arduino.h"
#include <vector>
struct WireFake {
	bool missing = false, error = false, fresh = true;
	uint8_t device = 0x69, address = 0, reg = 0;
	uint8_t registers[256]{};
	int16_t x = 100, y = 0, z = 0;
	int sda = -1, scl = -1;
	std::vector<uint8_t> tx, rx;
	unsigned index = 0;
	void begin(int a, int b) { sda = a; scl = b; }
	void setClock(int) {}
	void setClockStretchLimit(int) {}
	void beginTransmission(uint8_t addr) { address = addr; tx.clear(); }
	void write(uint8_t data) { tx.push_back(data); }
	int endTransmission(bool = true) {
		if (missing || error || address != device) return 2;
		reg = tx[0];
		if (tx.size() > 1) registers[reg] = tx[1];
		return 0;
	}
	int requestFrom(uint8_t, uint8_t size) {
		index = 0;
		if (reg == 0x0F) rx = {0xD3};
		else if (reg == 0x27) rx = {uint8_t(fresh ? 8 : 0)};
		else if (reg == 0xA8) rx = {uint8_t(x), uint8_t(uint16_t(x) >> 8), uint8_t(y), uint8_t(uint16_t(y) >> 8), uint8_t(z), uint8_t(uint16_t(z) >> 8)};
		else rx = {};
		return std::min(int(size), int(rx.size()));
	}
	uint8_t read() { return rx[index++]; }
};
inline WireFake Wire;
