        //codigo feito com objetivo de integrar os 2 modos do robo


        #include <WiFi.h>
        #include <WebServer.h>

        const char* ssid = "ERUS 2.4GHz";
        const char* password = "ultrabots3";

        WebServer server(80);

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

        

        #define distanciaMaxima 25

        long distanciaEsq;
        long distanciaDir;
        long distanciaFrontal;

        float correcaoMotorDireito = 10.3;

        // robo esta em modo automatico ou gestos
        bool modoAutomatico = true;

        // guarda o tempo do ultimo comando recebido
        unsigned long ultimoComando = 0;

        // tempo maximo sem receber comando antes de parar
        const int timeout = 1000;


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

        void frente(float velocidade){

        analogWrite(ENA, velocidade); //motor esquerdo
        analogWrite(ENB, velocidade - correcaoMotorDireito);//motor direito

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

        analogWrite(ENA, velocidade); //motor esquerdo
        analogWrite(ENB, velocidade - correcaoMotorDireito);//motor direito

        digitalWrite(esquerda1, HIGH);
        digitalWrite(esquerda2, LOW);

        digitalWrite(direita1, HIGH);
        digitalWrite(direita2, LOW);
        }

        void direita(float velocidade){

        analogWrite(ENA, velocidade); //motor esquerdo
        analogWrite(ENB, velocidade - correcaoMotorDireito);//motor direito

        digitalWrite(esquerda1, LOW);
        digitalWrite(esquerda2, HIGH);

        digitalWrite(direita1, LOW);
        digitalWrite(direita2, HIGH);
        }

        void re(float velocidade){

        analogWrite(ENA, velocidade); //motor esquerdo
        analogWrite(ENB, velocidade - correcaoMotorDireito);//motor direito

        digitalWrite(esquerda1, HIGH);
        digitalWrite(esquerda2, LOW);

        digitalWrite(direita1, LOW);
        digitalWrite(direita2, HIGH);
        }

        void receberComando(){

            String action = server.arg("action");

            ultimoComando = millis();


            Serial.println(action);


            if(action == "modo_auto"){

                modoAutomatico = true;

            }

            else if(action == "modo_gesto"){

                modoAutomatico = false;

            }

            if(!modoAutomatico){
                if(action == "frente"){
                    frente(70.0);
                }
                else if(action == "esquerda"){
                    esquerda(70.0);
                }
                else if(action == "direita"){
                    direita(70.0);
                }
                else if(action == "re"){
                    re(70.0);
                }
                else if(action == "parar"){
                    parar();
                }
            }

            server.send(200, "text/plain", "OK");
        }


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

            WiFi.begin(ssid, password);

            Serial.print("Ligando o Rádio"); // conectando no wifi

            while(WiFi.status() != WL_CONNECTED){

                delay(500);
                Serial.print(".");
            
            }
        
            Serial.println("");
            Serial.println("Radio Ligado"); // wifi conectado

            Serial.println("IP DO FUSCA: "); // ip do esp32
            Serial.println(WiFi.localIP());


            server.on("/cmd", receberComando); // cria rota para receber comandos

            server.begin(); // inicia o server
        


            Serial.println("Fusca Ligado e Fumaçando"); //servidor iniciado

            }

            void loop(){

            server.handleClient(); // processa requests vindos do python

            if(millis() - ultimoComando > timeout && !modoAutomatico){

                parar();

            }   

            if(modoAutomatico){

                distanciaEsq = medirDistancia(TRIG_ESQ, ECHO_ESQ);

                delay(30);

                distanciaDir = medirDistancia(TRIG_DIR, ECHO_DIR);

                delay(30);

                distanciaFrontal = min(distanciaEsq, distanciaDir);

            //Serial.println(distancia);

                if(distanciaFrontal < distanciaMaxima && distanciaFrontal != 999){

                    parar();
                    delay(1000);    

                    esquerda(70.0);
                    delay(600);
                }

                else{

                    frente(70.0);

                }

                delay(100);

                }
        }