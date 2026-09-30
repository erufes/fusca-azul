#pragma once
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
using std::min;
using std::max;
constexpr int LOW = 0, HIGH = 1, OUTPUT = 1;
inline uint32_t nowMs = 0;
inline int pins[32]{}, pwmRange = 0;
inline unsigned long millis() { return nowMs; }
inline void digitalWrite(int pin, int value) { pins[pin] = value; }
inline void pinMode(int, int) {}
inline void analogWriteRange(int range) { pwmRange = range; }
inline void analogWrite(int pin, int value) { pins[pin] = value; }
inline int constrain(int v, int lo, int hi) { return std::max(lo, std::min(v, hi)); }
struct SerialFake {
	std::string log;
	template<class... Args> void printf(const char* fmt, Args... args) {
		char buffer[512]; std::snprintf(buffer, sizeof(buffer), fmt, args...); log += buffer;
	}
};
inline SerialFake Serial;
