#include <Arduino.h>

#include "Robot.h"

namespace {
constexpr unsigned long MOVE_DURATION_MS = 2000;
constexpr unsigned long STOP_DURATION_MS = 1000;

Motor leftMotor(D5, D4, D3); // ENA, IN1, IN2
Motor rightMotor(D0, D2, D1); // ENB, IN3, IN4
Robot robot(leftMotor, rightMotor);
}

void setup() {
	robot.begin();
	Serial.begin(115200);
	Serial.println();
	Serial.println("[BOOT] Fusca Azul iniciado. Motores parados.");
	Serial.print("[BOOT] Motivo do reset: ");
	Serial.println(ESP.getResetReason());
}

void loop() {
	robot.forward();
	Serial.println("[MOTOR] Frente por 2 s");
	delay(MOVE_DURATION_MS);
	robot.stop();
	Serial.println("[MOTOR] Parado por 1 s");
	delay(STOP_DURATION_MS);
	robot.backward();
	Serial.println("[MOTOR] Re por 2 s");
	delay(MOVE_DURATION_MS);
	robot.stop();
	Serial.println("[MOTOR] Parado por 1 s");
	delay(STOP_DURATION_MS);
}
