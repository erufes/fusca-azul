#pragma once

#include <Arduino.h>

// Um canal da ponte H L298N, operando em velocidade total.
class Motor {
public:
	Motor(uint8_t enablePin, uint8_t input1Pin, uint8_t input2Pin);
	void begin();
	void forward();
	void backward();
	void stop();

private:
	void drive(uint8_t input1State, uint8_t input2State);

	const uint8_t enablePin_;
	const uint8_t input1Pin_;
	const uint8_t input2Pin_;
};
