#define TRIG 9
#define ECHO 10
#define ENA 3
#define ENB 11

#define esquerda1 8
#define esquerda2 7
#define direita1 5
#define direita2 6

#define distanciaMaxima 10

void setup() {
  Serial.begin(115200);

  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);

  pinMode(esquerda1, OUTPUT);
  pinMode(esquerda2, OUTPUT);
  pinMode(direita1, OUTPUT);
  pinMode(direita2, OUTPUT);

  pinMode(ENA, OUTPUT);
  pinMode(ENB, OUTPUT);


}

long medirDistancia() {
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);

  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);

  long duracao = pulseIn(ECHO, HIGH, 30000);

  if (duracao == 0) return 999; // evita erro

  return duracao * 0.034 / 2;
}

void frente(int velocidade) {
  analogWrite(ENA, velocidade);
  analogWrite(ENB, velocidade);  
  
  digitalWrite(esquerda1, HIGH);
  digitalWrite(esquerda2, LOW);
  digitalWrite(direita1, HIGH);
  digitalWrite(direita2, LOW);
}

void parar() {

  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
  
  digitalWrite(esquerda1, LOW);
  digitalWrite(esquerda2, LOW);
  digitalWrite(direita1, LOW);
  digitalWrite(direita2, LOW);
}

void esquerda(int velocidade) {
  analogWrite(ENA, velocidade);
  analogWrite(ENB, velocidade);

  digitalWrite(esquerda1, LOW);
  digitalWrite(esquerda2, HIGH);
  digitalWrite(direita1, HIGH);
  digitalWrite(direita2, LOW);
}

void loop() {

  long dist = medirDistancia();

  Serial.print("Distancia: ");
  Serial.println(dist);

  if (dist < distanciaMaxima) {
    parar();
    delay(1000);

    esquerda(70);
    delay(500);
  } else {
    frente(70);
  }

  delay(100);
}