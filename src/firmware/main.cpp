#include "GestosConnection.h"
#include "Robot.h"
#include "WifiConnection.h"
#include <Arduino.h>

namespace {
Motor leftMotor(D0, D2, D1);  // ENA, IN1, IN2
Motor rightMotor(D5, D3, D4); // ENB, IN3, IN4
Robot robot(leftMotor, rightMotor);
GestosConnection gestos(robot);
} // namespace

void setup() {
  Serial.begin(115200);
  robot.begin();
  Serial.printf("\n[BOOT] Fusca Azul: %s\n", ESP.getResetReason().c_str());
  WifiConnection::begin();
}

void loop() {
  robot.update();
  WifiConnection::update();
  gestos.update(WifiConnection::connected(), WifiConnection::hostname());
  delay(1);
}
