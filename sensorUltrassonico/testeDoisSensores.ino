// codigo destinado a adição de um ou mais sensores ao robô, com o objetivo de evitar pontos cegos


#define TRIG 9 // sensor frontal
#define ECHO 10 // sensor frontal

#define TRIG_ESQ 12 // sensor esquerdo
#define ECHO_ESQ 13 // sensor esquerdo

#define ENA 3
#define ENB 11

#define esquerda1 8 // IN1 (esquerda frente)
#define esquerda2 7 // IN2 (esquerda trás)
#define direita1 5 // IN3 (direita frente)
#define direita2 6 // IN4 (direita trás)

#define distanciaMaxima 20 //distancia do sensor bacana

long distancia;


long medirDistancia(int trig, int echo){ //agora o sensor escolhido é definido nos parametros quando chama a funcao
  digitalWrite(trig, LOW); 
  delayMicroseconds(2); 

  digitalWrite(trig, HIGH); // envia o pulso ultrassonico
  delayMicroseconds(10);

  digitalWrite(trig, LOW); 
  
  long duracao = pulseIn(echo, HIGH, 30000); 
  
  if (duracao == 0) return 999; // evita erro

  return duracao * 0.034 / 2; // converte pra cm, dividido por 2 pq o som vai e volta
}

void frente(int velocidade){ // a velocidade é definida no parametros quando chama a funcao
  analogWrite(ENA, velocidade);
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

void esquerda(int velocidade){ //aqui o robo gira no proprio lugar(quando nao tem pra onde ir)
  analogWrite(ENA, velocidade);
  analogWrite(ENB, velocidade);

  digitalWrite(esquerda1, LOW);
  digitalWrite(esquerda2, HIGH);
  digitalWrite(direita1, HIGH);
  digitalWrite(direita2, LOW);
}
)
void curvaEsquerda(int velFrente, int velMenor){ //a velocidade de cada roda e def no paramwtro
  analogWrite(ENA, velMenor); // roda esquerda gira mais lento
  analogWrite(ENB, velFrente);   // roda direita mais rápido
  
  digitalWrite(esquerda1, HIGH);
  digitalWrite(esquerda2, LOW);
  digitalWrite(direita1, HIGH);
  digitalWrite(direita2, LOW);
}

void setup(){
  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);

  pinMode(TRIG_ESQ, OUTPUT);
  pinMode(ECHO_ESQ, INPUT);

  pinMode(esquerda1, OUTPUT);
  pinMode(esquerda2, OUTPUT);
  pinMode(direita1, OUTPUT);
  pinMode(direita2, OUTPUT);

  pinMode(ENA, OUTPUT);
  pinMode(ENB, OUTPUT);

  Serial.begin(115200); // TEM QUE TA IGUAL NA IDE, PRA CONSEGUIR MONITORAR!!
}      

void loop(){

  
  long distFrente = medirDistancia(TRIG, ECHO); //aqui mede o sensor da frente
  delay(50);

  long distEsq = medirDistancia(TRIG_ESQ, ECHO_ESQ); // aqui ede o sensor da esquerda
  delay(50);

  Serial.print("Frente: ");
  Serial.print(distFrente);
  Serial.print(" | Esquerda: ");
  Serial.println(distEsq);

  if(distFrente < distanciaMaxima && distFrente != 999){ //se tiver obstaculo elle entra nesse if

    if(distEsq > distanciaMaxima){ //se a esq tiver livre ele faz uma curva mais dboa
      curvaEsquerda(80, 40);
    }
    else{
      esquerda(70); //mas se a esquerda tiver bloqueada tbm, ele vira parado
    }
  } 
  else{
    frente(80);
  }

  delay(50);
}