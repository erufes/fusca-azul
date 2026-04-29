#define TRIG // a definir entrada 
#define ECHO // a definir entrada 

#define IN1 // a definir entrada 
#define IN2 // a definir entrada 
#define IN3 // a definir entrada 
#define IN4 // a definir entrada 

void setup(){
  pinMode(TRIG, OUTPUT);
  pinMode(ECHO, INPUT);
  
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  Serial.begin(115200);
}

long distancia;

medirDistancia(){
  digitalWrite(TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG, LOW);
  
  long duracao = pulseIn(ECHO, HIGH);
  return duracao * 0.034 / 2;
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
      
void loop(){
  if(distancia < 15){
    parar();
    delay(300); // aq é em ms
    esquerda();
  }
    
  }
