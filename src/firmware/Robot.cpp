#include "Robot.h"

Robot::Robot(Motor& leftMotor, Motor& rightMotor)
	: leftMotor_(leftMotor), rightMotor_(rightMotor) {}

void Robot::begin() {
	leftMotor_.begin();
	rightMotor_.begin();
	state_.set("PARADO");
}

void Robot::forward() {
	leftMotor_.forward();
	rightMotor_.forward();
	state_.set("FRENTE");
}

void Robot::backward() {
	leftMotor_.backward();
	rightMotor_.backward();
	state_.set("RE");
}

void Robot::stop() {
	leftMotor_.stop();
	rightMotor_.stop();
	state_.set("PARADO");
}

void Robot::left() {
	leftMotor_.backward();
	rightMotor_.forward();
	state_.set("ESQUERDA");
}

void Robot::right() {
	leftMotor_.forward();
	rightMotor_.backward();
	state_.set("DIREITA");
}
