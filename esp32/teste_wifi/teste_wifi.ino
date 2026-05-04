#include <WiFi.h>
#include <WebServer.h>

#define LED_1 32

const char* ssid = "ERUS 2.4GHz";
const char* password = "ultrabots3";

WebServer server(80);

void handleCmd() {
  if (!server.hasArg("action")) {
    server.send(400, "text/plain", "Parametro 'action' ausente");
    return;
  }

  String action = server.arg("action");
  Serial.println("Comando recebido: " + action);

  if (action == "led_on") {
    digitalWrite(LED_1, HIGH);
    server.send(200, "text/plain", "LED ligado");
  } else if (action == "led_off") {
    digitalWrite(LED_1, LOW);
    server.send(200, "text/plain", "LED desligado");
  } else {
    server.send(400, "text/plain", "Acao desconhecida: " + action);
  }
}

void handleStatus() {
  String json = "{\"ip\":\"" + WiFi.localIP().toString() + "\",\"rssi\":" + WiFi.RSSI() + "}";
  server.send(200, "application/json", json);
}

void setup() {
  Serial.begin(115200);
  delay(20);

  Serial.println();
  Serial.print("Conectando em ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println();
  Serial.print("Conectado! IP: ");
  Serial.println(WiFi.localIP());

  pinMode(LED_1, OUTPUT);

  server.on("/cmd", handleCmd);
  server.on("/status", handleStatus);
  server.begin();
  Serial.println("Servidor HTTP iniciado na porta 80");
}

void loop() {
  server.handleClient();
}
