#pragma once

#include "Motor.h"

class Robot {
public:
	Robot(Motor& leftMotor, Motor& rightMotor);
	void begin();
	void forward();
	void backward();
	void stop();

private:
	Motor& leftMotor_;
	Motor& rightMotor_;
};
