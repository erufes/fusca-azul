#include "Gy80.h"
#include <Wire.h>
#include <cmath>

namespace {
// The installed module has +X pointing up; use -1 if -X points up.
constexpr uint8_t YAW_AXIS = 0; // X=0, Y=1, Z=2.
constexpr float YAW_SIGN = 1.0f;
constexpr float DPS_PER_LSB = 0.00875f; // L3G4200D, +/-250 degrees/s.
}

bool Gy80::read(uint8_t reg, uint8_t* data, uint8_t size) {
	Wire.beginTransmission(address_);
	Wire.write(reg);
	if (Wire.endTransmission(false) != 0) return false;
	if (Wire.requestFrom(address_, size) != size) return false;
	for (uint8_t i = 0; i < size; ++i) data[i] = Wire.read();
	return true;
}

bool Gy80::write(uint8_t reg, uint8_t value) {
	Wire.beginTransmission(address_);
	Wire.write(reg);
	Wire.write(value);
	return Wire.endTransmission() == 0;
}

void Gy80::fail(const char* reason) {
	failed_ = true;
	calibrated_ = false;
	state_.set("FALHA", reason);
}

void Gy80::begin(uint8_t sda, uint8_t scl) {
	Wire.begin(sda, scl);
	Wire.setClock(100000);
	Wire.setClockStretchLimit(1500);
	uint8_t identity = 0;
	for (uint8_t candidate : {0x68, 0x69}) {
		address_ = candidate;
		if (read(0x0F, &identity, 1) && identity == 0xD3) break;
		address_ = 0;
	}
	if (!address_) { fail("L3G4200D nao encontrado em 0x68/0x69; confira SDA/SCL"); return; }
	// BDU, little endian, 250 dps; no high-pass or FIFO; 100 Hz, all axes.
	if (!write(0x20, 0x00) || !write(0x21, 0x00) || !write(0x22, 0x00) ||
		!write(0x23, 0x80) || !write(0x24, 0x00) || !write(0x2E, 0x00) || !write(0x20, 0x0F)) {
		fail("Erro ao configurar giroscopio"); return;
	}
	started_ = lastSample_ = lastPoll_ = millis();
	state_.set("CALIBRANDO", "Mantenha o robo imovel por cerca de 3 segundos");
	Serial.printf("[GY80] L3G4200D em 0x%02X; eixo X, sinal %.0f\n", address_, YAW_SIGN);
}

bool Gy80::update(bool moving) {
	uint32_t now = millis();
	if (failed_ || now - started_ < 250) return false;
	if (!calibrated_ && now - started_ > 10000) { fail("Calibracao instavel; imobilize e reinicie"); return false; }
	if (now - lastPoll_ < 10) return false;
	lastPoll_ = now;
	if (calibrated_ && moving && now - lastSample_ > 100) { fail("Leitura atrasada mais de 100 ms"); return false; }
	uint8_t status, bytes[6];
	if (!read(0x27, &status, 1)) { fail("Erro I2C lendo status"); return false; }
	if (!(status & 0x08)) {
		if (now - lastSample_ > 500) fail("Giroscopio sem novas amostras");
		return false;
	}
	if (!read(0x28 | 0x80, bytes, 6)) { fail("Leitura I2C incompleta"); return false; }
	float axes[3];
	for (int i = 0; i < 3; ++i) {
		int16_t raw = static_cast<int16_t>(bytes[2*i] | (uint16_t(bytes[2*i+1]) << 8));
		if (std::abs(int(raw)) > 32000) { fail("Giroscopio saturado"); return false; }
		axes[i] = raw * DPS_PER_LSB;
	}
	// Discovery may block while stopped; never integrate that unobserved interval.
	dt_ = now - lastSample_ <= 100 ? (now - lastSample_) / 1000.0f : 0;
	lastSample_ = now;
	if (!calibrated_) {
		bool moving = false;
		for (int i = 0; i < 3; ++i) {
			if (!samples_) minimum_[i] = maximum_[i] = axes[i];
			minimum_[i] = min(minimum_[i], axes[i]);
			maximum_[i] = max(maximum_[i], axes[i]);
			if (maximum_[i] - minimum_[i] > 3.0f || std::abs(axes[i]) > 15.0f) moving = true;
		}
		if (moving) { samples_ = 0; sum_ = 0; return false; }
		sum_ += axes[YAW_AXIS];
		if (++samples_ >= 200) {
			bias_ = sum_ / samples_;
			calibrated_ = true;
			state_.set("PRONTO");
			Serial.printf("[GY80] Bias X: %.3f graus/s\n", bias_);
		}
		return false;
	}
	rate_ = YAW_SIGN * (axes[YAW_AXIS] - bias_);
	return true;
}
