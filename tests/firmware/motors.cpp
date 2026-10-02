#include "Robot.h"
#include <cassert>

int main() {
	Motor lm(0, 1, 2), rm(3, 4, 5);
	Robot robot(lm, rm);
	robot.begin();
	assert(pwmRange == 1024 && pins[0] == 0 && pins[3] == 0);
	// Motion works immediately, without a sensor or calibration.
	robot.forward();
	assert(pins[0] == 1024 && pins[3] == 1024);
	assert(pins[1] == HIGH && pins[2] == LOW && pins[4] == HIGH && pins[5] == LOW);
	robot.backward();
	assert(pins[0] == 1024 && pins[3] == 1024);
	assert(pins[1] == LOW && pins[2] == HIGH && pins[4] == LOW && pins[5] == HIGH);
	robot.left();
	assert(pins[0] == 1024 && pins[3] == 1024);
	assert(pins[1] == LOW && pins[2] == HIGH && pins[4] == HIGH && pins[5] == LOW);
	robot.right();
	assert(pins[0] == 1024 && pins[3] == 1024);
	assert(pins[1] == HIGH && pins[2] == LOW && pins[4] == LOW && pins[5] == HIGH);
	// Repeated commands renew the watchdog, including across millis rollover.
	nowMs = UINT32_MAX - 200;
	robot.forward();
	nowMs += 300;
	robot.update();
	assert(pins[0] == 1024 && pins[3] == 1024);
	robot.forward();
	nowMs += 399;
	robot.update();
	assert(pins[0] == 1024 && pins[3] == 1024);
	nowMs += 1;
	robot.update();
	assert(pins[0] == 0 && pins[3] == 0);
	robot.forward();
	robot.stop();
	assert(pins[0] == 0 && pins[3] == 0);
	assert(pins[1] == LOW && pins[2] == LOW && pins[4] == LOW && pins[5] == LOW);
	lm.forward(); assert(pins[0] == 1024);
	lm.backward(); assert(pins[0] == 1024);
	lm.forward(2000); assert(pins[0] == 1024);
	lm.forward(-1); assert(pins[0] == 0);
}
