// CODIGO FEITO POR yagwDev

#define TRIG 27 //sensor
#define ECHO 26 //sensor

#define ENA 17
#define ENB 23

#define esquerda1 18 //IN1 (esquerda frente)
#define esquerda2 19 //IN2 (esquerda trás)
#define direita1 21 //IN3 (direita frente)
#define direita2 22 //IN4 (direita trás)

#define distanciaMaxima 20 // distancia do sensor

long distancia;

long medirDistancia(){

  digitalWrite(TRIG, LOW); // comeca desligado
  delayMicroseconds(2);

  digitalWrite(TRIG, HIGH); // envia o pulso de 10 microssegundos
  delayMicroseconds(10);

  digitalWrite(TRIG, LOW); // termina o pulso

  long duracao = pulseIn(ECHO, HIGH, 30000);

  if(duracao == 0) return 999; // evita erro se nao tiver leitura

  return duracao * 0.034 / 2;
}

void frente(int velocidade){

  analogWrite(ENA, velocidade);      // motor esquerdo
  analogWrite(ENB, velocidade - 15); // motor direito corrigido

  digitalWrite(esquerda1, LOW);
  digitalWrite(esquerda2, HIGH);

  digitalWrite(direita1, HIGH);
  digitalWrite(direita2, LOW);
}

void parar(){

  analogWrite(ENA, 0);
  analogWrite(ENB, 0);

  digitalWrite(esquerda1, LOW);
  digitalWrite(esquerda2, LOW);

  digitalWrite(direita1, LOW);
  digitalWrite(direita2, LOW);
}

void esquerda(int velocidade){

  analogWrite(ENA, velocidade);
  analogWrite(ENB, velocidade);

  digitalWrite(esquerda1, HIGH);
  digitalWrite(esquerda2, LOW);

  digitalWrite(direita1, HIGH);
  digitalWrite(direita2, LOW);
}

void direita(int velocidade){

  analogWrite(ENA, velocidade);
  analogWrite(ENB, velocidade);

  digitalWrite(esquerda1, HIGH);
  digitalWrite(esquerda2, LOW);

  digitalWrite(direita1, LOW);
  digitalWrite(direita2, HIGH);
}

void setup(){

  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);

  pinMode(esquerda1, OUTPUT);
  pinMode(esquerda2, OUTPUT);

  pinMode(direita1, OUTPUT);
  pinMode(direita2, OUTPUT);

  pinMode(ENA, OUTPUT);
  pinMode(ENB, OUTPUT);

  Serial.begin(115200);
}

void loop(){

  distancia = medirDistancia();

  Serial.println(distancia);

  if(distancia < distanciaMaxima && distancia != 999){

    parar();
    delay(1000);

    esquerda(70);
    delay(500);
  }

  else{

    frente(70);
  }

  delay(100);
}
