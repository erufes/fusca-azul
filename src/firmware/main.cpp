#include <Arduino.h>
#include <Wire.h>
#include <VL53L0X.h>

// CJVL53L0XV2: VIN em 3V3, GND em GND, SDA em D2 e SCL em D1.
constexpr uint8_t SDA_PIN = D2; // GPIO4
constexpr uint8_t SCL_PIN = D1; // GPIO5
constexpr uint16_t SENSOR_TIMEOUT_MS = 500;
constexpr unsigned long MEASUREMENT_INTERVAL_MS = 500;

VL53L0X sensor;

void setup() {
    Serial.begin(115200);
    Wire.begin(SDA_PIN, SCL_PIN);
    sensor.setTimeout(SENSOR_TIMEOUT_MS);
    Serial.println("Fusca Azul - leitura do VL53L0X");

    if (!sensor.init()) {
        while (true) {
            Serial.println("Falha ao iniciar VL53L0X. Verifique a ligacao e reinicie.");
            delay(1000);
        }
    }
}

void loop() {
    const uint16_t distanceMm = sensor.readRangeSingleMillimeters();

    if (sensor.timeoutOccurred()) {
        Serial.println("Timeout na leitura do VL53L0X");
    } else if (distanceMm >= 8190) {
        Serial.println("Leitura invalida ou fora de alcance");
    } else {
        Serial.print("Distancia: ");
        Serial.print(distanceMm);
        Serial.print(" mm (");
        Serial.print(distanceMm / 10.0f, 1);
        Serial.println(" cm)");
    }

    delay(MEASUREMENT_INTERVAL_MS);
}
