#pragma once

#include <Arduino.h>

// Um canal da ponte H L298N, com PWM de até 100% no enable.
class Motor {
public:
	static constexpr int MAX_PWM = 1024;
	Motor(uint8_t enablePin, uint8_t input1Pin, uint8_t input2Pin);
	void begin();
	void forward(int pwm = MAX_PWM);
	void backward(int pwm = MAX_PWM);
	void stop();

private:
	void drive(uint8_t input1State, uint8_t input2State, int pwm);

	int lastPwm_ = 0;
	uint8_t lastInput1_ = LOW, lastInput2_ = LOW;
	const uint8_t enablePin_;
	const uint8_t input1Pin_;
	const uint8_t input2Pin_;
};
