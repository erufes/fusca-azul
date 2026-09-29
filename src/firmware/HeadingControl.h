#pragma once
#include <cmath>

// Positive yaw is a left turn, viewed from above. PWM units: 0..1024.
class HeadingControl {
public:
	static constexpr int BASE_PWM = 512;
	static constexpr int MAX_TRIM = 154;
	void reset() { heading_ = 0; }
	int update(float rate, float dt) {
		heading_ = limit(heading_ + rate * dt, 30.0f);
		return static_cast<int>(limit(8.0f * heading_ + 2.0f * rate, MAX_TRIM));
	}
	static void mix(int direction, int trim, int& left, int& right) {
		trim = static_cast<int>(limit(trim, MAX_TRIM));
		// Reverse travel needs the opposite wheel slowed for the same yaw error.
		left = BASE_PWM - (direction * trim < 0 ? std::abs(trim) : 0);
		right = BASE_PWM - (direction * trim > 0 ? std::abs(trim) : 0);
	}
private:
	static float limit(float value, float bound) {
		return value > bound ? bound : (value < -bound ? -bound : value);
	}
	float heading_ = 0;
};
