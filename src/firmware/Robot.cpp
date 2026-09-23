#include "Robot.h"

Robot::Robot(Motor& leftMotor, Motor& rightMotor)
	: leftMotor_(leftMotor), rightMotor_(rightMotor) {}

void Robot::begin() {
	leftMotor_.begin();
	rightMotor_.begin();
}

void Robot::forward() {
	leftMotor_.forward();
	rightMotor_.forward();
}

void Robot::backward() {
	leftMotor_.backward();
	rightMotor_.backward();
}

void Robot::stop() {
	leftMotor_.stop();
	rightMotor_.stop();
}
