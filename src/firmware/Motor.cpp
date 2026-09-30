#include "Motor.h"

namespace {
constexpr uint32_t PWM_RANGE = 1024;
constexpr int MOTOR_PWM = PWM_RANGE / 2;
}

Motor::Motor(uint8_t enablePin, uint8_t input1Pin, uint8_t input2Pin)
	: enablePin_(enablePin), input1Pin_(input1Pin), input2Pin_(input2Pin) {}

void Motor::begin() {
	analogWriteRange(PWM_RANGE);
	digitalWrite(enablePin_, LOW);
	pinMode(enablePin_, OUTPUT);
	digitalWrite(input1Pin_, LOW);
	digitalWrite(input2Pin_, LOW);
	pinMode(input1Pin_, OUTPUT);
	pinMode(input2Pin_, OUTPUT);
	stop();
}

void Motor::forward(int pwm) {
	drive(HIGH, LOW, pwm);
}

void Motor::backward(int pwm) {
	drive(LOW, HIGH, pwm);
}

void Motor::stop() {
	lastPwm_ = 0;
	lastInput1_ = lastInput2_ = LOW;
	analogWrite(enablePin_, 0);
	digitalWrite(input1Pin_, LOW);
	digitalWrite(input2Pin_, LOW);
}

void Motor::drive(uint8_t input1State, uint8_t input2State, int pwm) {
	pwm = constrain(pwm, 0, MOTOR_PWM);
	if (pwm == lastPwm_ && input1State == lastInput1_ && input2State == lastInput2_) return;
	if (input1State != lastInput1_ || input2State != lastInput2_) analogWrite(enablePin_, 0);
	digitalWrite(input1Pin_, input1State);
	digitalWrite(input2Pin_, input2State);
	analogWrite(enablePin_, pwm);
	lastPwm_ = pwm;
	lastInput1_ = input1State;
	lastInput2_ = input2State;
}
