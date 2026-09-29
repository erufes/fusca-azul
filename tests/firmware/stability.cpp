#include "Robot.h"
#include <Wire.h>
#include <cassert>

void tick(Robot& robot, unsigned ms = 10) { nowMs += ms; robot.update(); }
void calibrate(Robot& robot, Gy80& gyro) {
	for (int i = 0; i < 230; ++i) tick(robot);
	assert(gyro.ready());
}
int main() {
	HeadingControl heading;
	int left, right;
	int trim = heading.update(5, .01f);
	assert(trim > 0);
	HeadingControl::mix(1, trim, left, right);
	assert(left == 512 && right < left);
	HeadingControl::mix(-1, trim, left, right);
	assert(right == 512 && left < right);
	heading.reset();
	assert(heading.update(0, .01f) == 0);
	for (int direction : {-1, 1}) for (int t : {-10000, -50, 0, 50, 10000}) {
		HeadingControl::mix(direction, t, left, right);
		assert(left >= 358 && left <= 512 && right >= 358 && right <= 512);
	}
	// Closed-loop simulation: the right motor is 10% stronger, in both directions.
	for (int direction : {-1, 1}) {
		HeadingControl controller;
		float rate = 0;
		int l = 512, r = 512;
		for (int i = 0; i < 2000; ++i) {
			rate = direction * (1.1f * r - l) * 0.05f;
			HeadingControl::mix(direction, controller.update(rate, .01f), l, r);
		}
		assert(std::abs(rate) < .1f);
		assert(l == 512 && r < 512);
	}
	Gy80 gyro; Motor lm(0, 1, 2), rm(3, 4, 5); Robot robot(lm, rm, gyro);
	robot.begin(); gyro.begin(13, 15);
	assert(Wire.sda == 13 && Wire.scl == 15);
	assert(Wire.registers[0x23] == 0x80 && Wire.registers[0x20] == 0x0F);
	robot.forward(); assert(pins[0] == 0 && pins[3] == 0);
	calibrate(robot, gyro);
	// Calibrated bias is removed, rather than interpreted as a turn.
	robot.forward(); tick(robot);
	assert(pins[0] == 512 && pins[3] == 512);
	// Rotation about horizontal Y/Z must not cause a yaw correction.
	Wire.y = 500; Wire.z = -700; tick(robot);
	assert(pins[0] == 512 && pins[3] == 512);
	Wire.x = 1100; tick(robot);
	assert(pins[0] == 512 && pins[3] < 512);
	int old = pins[3]; robot.forward(); tick(robot);
	assert(pins[3] <= old); // Repeated forward must preserve accumulated heading.
	robot.backward(); tick(robot);
	assert(pins[0] < 512 && pins[3] == 512);
	assert(pins[1] == LOW && pins[2] == HIGH);
	robot.left(); tick(robot);
	assert(pins[0] == 512 && pins[3] == 512); // Manual turn is not counteracted.
	robot.stop(); assert(pins[0] == 0 && pins[3] == 0);
	tick(robot, 2000); assert(gyro.ready()); // mDNS pause while stopped is harmless.
	robot.forward(); Wire.error = true; tick(robot);
	assert(!gyro.ready() && pins[0] == 0 && pins[3] == 0);
	robot.forward(); assert(pins[0] == 0 && pins[3] == 0);
	Wire = WireFake{};
	Gy80 timeoutGyro; Robot timeoutRobot(lm, rm, timeoutGyro);
	timeoutRobot.begin(); timeoutGyro.begin(13, 15); calibrate(timeoutRobot, timeoutGyro);
	timeoutRobot.forward(); tick(timeoutRobot, 110);
	assert(!timeoutGyro.ready() && pins[0] == 0 && pins[3] == 0);
	Wire = WireFake{};
	Gy80 commandGyro; Robot commandRobot(lm, rm, commandGyro);
	commandRobot.begin(); commandGyro.begin(13, 15); calibrate(commandRobot, commandGyro);
	commandRobot.forward();
	for (int i = 0; i < 41; ++i) tick(commandRobot);
	assert(commandGyro.ready() && pins[0] == 0 && pins[3] == 0);
	// Motion during calibration must not silently become a gyro offset.
	Wire = WireFake{};
	Gy80 disturbed; disturbed.begin(13, 15);
	for (int i = 0; i < 1100; ++i) {
		Wire.x = i % 2 ? 100 : 1000;
		nowMs += 10; disturbed.update();
	}
	assert(!disturbed.ready());
	Wire.missing = true;
	Gy80 absent; absent.begin(13, 15); assert(!absent.ready());
}
