#pragma once

#include "Motor.h"
#include "StateLog.h"
#include "Gy80.h"
#include "HeadingControl.h"

class Robot {
public:
	Robot(Motor& leftMotor, Motor& rightMotor, Gy80& gyro);
	void update();
	void begin();
	void forward();
	void backward();
	void stop();
	void left();
	void right();

private:
	enum class Motion { Stop, Forward, Backward, Left, Right };
	void command(Motion next);
	void drive(int left, int right);
	Motion motion_ = Motion::Stop;
	Gy80& gyro_;
	HeadingControl heading_;
	StateLog stabilization_{"RUMO"};
	uint32_t lastCommand_ = 0;
	StateLog state_{"ROBO"};
	Motor& leftMotor_;
	Motor& rightMotor_;
};
