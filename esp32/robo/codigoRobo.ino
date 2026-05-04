// CODIGO FEITO POR yagwDev

#define TRIG 9 //sensor
#define ECHO 10 //sensor

#define ENA 3
#define ENB 11

#define esquerda1 8 //IN1 (esquerda frente)
#define esquerda2 7 //IN2 (esquerda trás)
#define direita1 5 //IN3 (direita frente)
#define direita2 6 //IN4 (direita trás)

#define distanciaMaxima 10 // distancia do sensor

long distancia;

long medirDistancia(){
  digitalWrite(TRIG, LOW); // comeca desligado
  delayMicroseconds(2); 

  digitalWrite(TRIG, HIGH); // envia o pulso de 10 microssegundos (faz disparar um som ultrassonico)
  delayMicroseconds(10);

  digitalWrite(TRIG, LOW); // termina o pulso
  
  long duracao = pulseIn(ECHO, HIGH, 30000); // pulsein calcula quanto tempo o pino ECHO ficou em HIGH (enquanto o som ta indo e voltando), ele espera no máximo 30 microssegundos
  
  if (duracao == 0) return 999; // evita erro se nao tiver leitura

  return duracao * 0.034 / 2; // 0.034 = velocidade do som em cm por microsegundo divide por 2 porque o som vai e volta
}

void frente(int velocidade) { //o parametro de velocidade é definido quando chama a funcao,
  analogWrite(ENA, velocidade);// ex: frente(100), a velocidade do motor vai ser 100 de 255 que seria o maximo
  analogWrite(ENB, velocidade);  
  
  digitalWrite(esquerda1, HIGH);
  digitalWrite(esquerda2, LOW);
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

void esquerda(int velocidade) {
  analogWrite(ENA, velocidade);
  analogWrite(ENB, velocidade);

  digitalWrite(esquerda1, LOW);
  digitalWrite(esquerda2, HIGH);
  digitalWrite(direita1, HIGH);
  digitalWrite(direita2, LOW);
}

void direita(int velocidade){ //nao usado, mas adicionei por desencargo de consciencia
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

  Serial.begin(115200); //bits por segundo, O VALOR TEM QUE BATER COM O MONITOR SERIAL PRA CONSEGUIR MONITORAR!!!
}      

void loop(){

  distancia = medirDistancia();
  
  Serial.println(distancia); // printa a distancia

  if(distancia < distanciaMaxima && distancia != 999){ //quando o robo nao detecta nada na frente dele, ele retorna 999, entao aqui ignoramos isso
    parar();
    delay(1000); // aq é em ms

    esquerda(70); //velocidade
    delay(500); // aq é em ms
  } 
  else{
    frente(70);//velocidade
  }
  delay(100);
}
