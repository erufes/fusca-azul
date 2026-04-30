#define TRIG 9
#define ECHO 10

void setup() {
  Serial.begin(115200);
  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);
}

void loop() {
  // Garante sinal limpo
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);

  // Dispara o sensor (10 µs)
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);

  // Lê o tempo do eco
  long duracao = pulseIn(ECHO, HIGH);

  // Converte pra distância (cm)
  float distancia = duracao * 0.034 / 2;

  // DEBUG no Serial
  Serial.print("Duracao: ");
  Serial.print(duracao);
  Serial.print(" us | Distancia: ");
  Serial.print(distancia);
  Serial.println(" cm");

  delay(500);
}