// CODIGO FEITO POR yagwDev

#define TRIG_ESQ 27
#define ECHO_ESQ 33

#define TRIG_DIR 26
#define ECHO_DIR 32

#define ENA 17
#define ENB 23

#define esquerda1 18 // IN1
#define esquerda2 19 // IN2

#define direita1 21 // IN3
#define direita2 22 // IN4

float correcaoMotorDireito = 10.5;

#define distanciaMaxima 10

long distanciaEsq;
long distanciaDir;
long distanciaFrontal;


// =====================================
// FUNCAO SENSOR
// =====================================

long medirDistancia(int trigPin, int echoPin){

  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);

  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);

  digitalWrite(trigPin, LOW);

  long duracao = pulseIn(echoPin, HIGH, 30000);

  if(duracao == 0) return 999;

  return duracao * 0.034 / 2;
}


// =====================================
// MOVIMENTOS
// =====================================

void frente(float velocidade){

    analogWrite(ENA, velocidade);
    analogWrite(ENB, velocidade - correcaoMotorDireito);

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

void esquerda(float velocidade){

    analogWrite(ENA, velocidade);
    analogWrite(ENB, velocidade - correcaoMotorDireito);

    digitalWrite(esquerda1, HIGH);
    digitalWrite(esquerda2, LOW);

    digitalWrite(direita1, HIGH);
    digitalWrite(direita2, LOW);
}

void direita(float velocidade){

    analogWrite(ENA, velocidade);
    analogWrite(ENB, velocidade - correcaoMotorDireito);

    digitalWrite(esquerda1, LOW);
    digitalWrite(esquerda2, HIGH);

    digitalWrite(direita1, LOW);
    digitalWrite(direita2, HIGH);
}

void re(float velocidade){

    analogWrite(ENA, velocidade);
    analogWrite(ENB, velocidade - correcaoMotorDireito);

    digitalWrite(esquerda1, HIGH);
    digitalWrite(esquerda2, LOW);

    digitalWrite(direita1, LOW);
    digitalWrite(direita2, HIGH);
}


// =====================================
// SETUP
// =====================================

void setup(){

    pinMode(TRIG_ESQ, OUTPUT);
    pinMode(ECHO_ESQ, INPUT);

    pinMode(TRIG_DIR, OUTPUT);
    pinMode(ECHO_DIR, INPUT);

    pinMode(esquerda1, OUTPUT);
    pinMode(esquerda2, OUTPUT);

    pinMode(direita1, OUTPUT);
    pinMode(direita2, OUTPUT);

    pinMode(ENA, OUTPUT);
    pinMode(ENB, OUTPUT);

    Serial.begin(115200);
}


// =====================================
// LOOP
// =====================================

void loop(){

    distanciaEsq = medirDistancia(TRIG_ESQ, ECHO_ESQ);

    delay(30);

    distanciaDir = medirDistancia(TRIG_DIR, ECHO_DIR);

    delay(30);

    distanciaFrontal = min(distanciaEsq, distanciaDir);


    // DEBUG SERIAL

    Serial.print("Esq: ");
    Serial.print(distanciaEsq);

    Serial.print(" | Dir: ");
    Serial.print(distanciaDir);

    Serial.print(" | Frente: ");
    Serial.println(distanciaFrontal);


    // LOGICA DO ROBO

    if(distanciaFrontal < distanciaMaxima &&
       distanciaFrontal != 999){

        parar();
        delay(1000);

        esquerda(70.0);
        delay(500);
    }

    else{

        frente(70.0);
    }

    delay(100);
}