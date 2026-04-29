#define TRIG // a definir entrada
#define ECHO // a definir entrada

#define IN1 // a definir entrada
#define IN2 // a definir entrada
#define IN3 // a definir entrada
#define IN4 // a definir entrada

long distancia;

long medirDistancia(){
  digitalWrite(TRIG, LOW); // comeca desligado
  delayMicroseconds(2); 

  digitalWrite(TRIG, HIGH); // envia o pulso de 10 ms (faz disparar um som ultrassonico)
  delayMicroseconds(10);

  digitalWrite(TRIG, LOW); // termina o pulso
  
  long duracao = pulseIn(ECHO, HIGH, 30000); // pulsein calcula quanto tempo o pino ECHO ficou em HIGH, ele espera no máximo 30ms
  
  if (duracao == 0) return 999; // evita erro se nao tiver leitura

  return duracao * 0.034 / 2; // 0.034 = velocidade do som em cm por microsegundo divide por 2 porque o som vai e volta
}

void frente(){
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
} 
  
void parar(){
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}

void esquerda(){
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void direita(){
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
} 

void setup(){
  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);
  
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT); 
  pinMode(IN4, OUTPUT);

  Serial.begin(115200);
}      

void loop(){

  distancia = medirDistancia();
  
  Serial.println(distancia); // printa a distancia

  if(distancia < 20 && distancia != 999){
    parar();
    delay(300); // aq é em ms
    esquerda();
    delay(400); // aq é em ms
  } 
  else{
    frente();
  }
}