//codigo feito por yagwDev

#define TRIG 9
#define ECHO 10
#define LED 7
#define distanciaMaxima 10

void setup() {
  Serial.begin(115200);

  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);
  pinMode(LED, OUTPUT);
}

void loop() {

  // limpa o sinal
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);

  // dispara o pulso
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);

  long duracao = pulseIn(ECHO, HIGH, 30000);

  // filtro de erro
  if (duracao == 0) {
    Serial.println("Sem leitura");
    digitalWrite(LED, LOW);
    delay(200);
    return;
  }

  float distancia = duracao * 0.034 / 2;

  Serial.print("Distancia: ");
  Serial.print(distancia);
  Serial.println(" cm");

  // lógica do LED liga e desliga
  if (distancia > 0 && distancia < distanciaMaxima) {
    digitalWrite(LED, HIGH);
  } else {
    digitalWrite(LED, LOW);
  }

  delay(200);
}