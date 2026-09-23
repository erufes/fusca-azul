#include "Motor.h"

Motor::Motor(uint8_t enablePin, uint8_t input1Pin, uint8_t input2Pin)
	: enablePin_(enablePin), input1Pin_(input1Pin), input2Pin_(input2Pin) {}

void Motor::begin() {
	digitalWrite(enablePin_, LOW);
	pinMode(enablePin_, OUTPUT);
	digitalWrite(input1Pin_, LOW);
	digitalWrite(input2Pin_, LOW);
	pinMode(input1Pin_, OUTPUT);
	pinMode(input2Pin_, OUTPUT);
	stop();
}

void Motor::forward() {
	drive(HIGH, LOW);
}

void Motor::backward() {
	drive(LOW, HIGH);
}

void Motor::stop() {
	digitalWrite(enablePin_, LOW);
	digitalWrite(input1Pin_, LOW);
	digitalWrite(input2Pin_, LOW);
}

void Motor::drive(uint8_t input1State, uint8_t input2State) {
	digitalWrite(enablePin_, LOW);
	digitalWrite(input1Pin_, input1State);
	digitalWrite(input2Pin_, input2State);
	digitalWrite(enablePin_, HIGH);
}
