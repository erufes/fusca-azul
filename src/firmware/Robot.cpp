#include "Robot.h"

Robot::Robot(Motor& leftMotor, Motor& rightMotor)
	: leftMotor_(leftMotor), rightMotor_(rightMotor) {}

void Robot::begin() {
	leftMotor_.begin();
	rightMotor_.begin();
	state_.set("PARADO");
}

void Robot::command(Motion next) {
	lastCommand_ = millis();
	if (motion_ == next) return;
	motion_ = next;
	const char* label = next == Motion::Forward ? "FRENTE" : next == Motion::Backward ? "RE" :
		next == Motion::Left ? "ESQUERDA" : "DIREITA";
	state_.set(label);
	drive(Motor::MAX_PWM, Motor::MAX_PWM);
}

void Robot::forward() { command(Motion::Forward); }
void Robot::backward() { command(Motion::Backward); }
void Robot::left() { command(Motion::Left); }
void Robot::right() { command(Motion::Right); }

void Robot::stop() {
	motion_ = Motion::Stop;
	leftMotor_.stop();
	rightMotor_.stop();
	state_.set("PARADO");
}

void Robot::drive(int left, int right) {
	if (motion_ == Motion::Forward || motion_ == Motion::Right) leftMotor_.forward(left);
	else leftMotor_.backward(left);
	if (motion_ == Motion::Forward || motion_ == Motion::Left) rightMotor_.forward(right);
	else rightMotor_.backward(right);
}

void Robot::update() {
	if (motion_ != Motion::Stop && millis() - lastCommand_ >= 400) stop();
}
