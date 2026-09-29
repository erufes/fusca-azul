#pragma once

#include "Motor.h"
#include "StateLog.h"

class Robot {
public:
	Robot(Motor& leftMotor, Motor& rightMotor);
	void begin();
	void forward();
	void backward();
	void stop();
	void left();
	void right();

private:
	StateLog state_{"ROBO"};
	Motor& leftMotor_;
	Motor& rightMotor_;
};
