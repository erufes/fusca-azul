#pragma once

#include <Arduino.h>

// Um canal da ponte H L298N, com PWM limitado a 50% no enable.
class Motor {
public:
	Motor(uint8_t enablePin, uint8_t input1Pin, uint8_t input2Pin);
	void begin();
	void forward(int pwm = 512);
	void backward(int pwm = 512);
	void stop();

private:
	void drive(uint8_t input1State, uint8_t input2State, int pwm);

	int lastPwm_ = 0;
	uint8_t lastInput1_ = LOW, lastInput2_ = LOW;
	const uint8_t enablePin_;
	const uint8_t input1Pin_;
	const uint8_t input2Pin_;
};
