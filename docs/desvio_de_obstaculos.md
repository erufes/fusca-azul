# 🚧 Desvio de obstáculos

Modo autônomo no qual o robô se desloca sozinho, detectando obstáculos por sensores ultrassônicos e executando manobras de desvio em tempo real.

A lógica roda inteiramente no **ESP32**, que processa as leituras dos sensores **HC-SR04** e aciona os motores através de uma **ponte H**. Enquanto o caminho está livre, o robô avança; ao identificar um obstáculo dentro do limite de distância, decide entre parar, recuar ou desviar.

## Configuração dos sensores

Durante o desenvolvimento, foram realizados testes com diferentes configurações de sensores para avaliar a melhor estratégia de detecção de obstáculos:  

- 🔹 **1 sensor:** funcionamento simples e direto, porém com limitação na detecção lateral, reduzindo a precisão dos desvios.  
- 🔹 **2 sensores:** melhor equilíbrio entre custo, complexidade e eficiência, permitindo detecção mais confiável e decisões de desvio mais estáveis.  
- 🔹 **3 sensores:** maior cobertura de detecção, porém com aumento da complexidade de leitura e necessidade de maior calibração do sistema.  

A configuração com **2 sensores frontais apresentou o melhor custo-benefício**, sendo a solução mais estável e eficiente para o comportamento de desvio automático do robô.  

## Lógica de desvio

A cada ciclo do `loop()`, o ESP32 lê a distância dos dois sensores (`distanciaEsq` e `distanciaDir`) e considera como **distância frontal** o menor valor entre os dois — assim, qualquer obstáculo detectado de um lado ou de outro é tratado como obstáculo à frente.

O fluxo é simples e determinístico:

1. Mede a distância dos sensores esquerdo e direito.
2. Calcula a distância frontal: `min(distanciaEsq, distanciaDir)`.
3. **Se a distância for menor que o limite** (e diferente de `999`, valor usado para indicar leitura inválida): para o robô por 1 segundo e gira para a esquerda por 600 ms.
4. **Caso contrário:** segue em frente.

Não há lógica de decisão entre virar à esquerda ou à direita — o desvio é sempre feito para a esquerda. Após a manobra, o ciclo recomeça e o robô reavalia se o caminho está livre.

## Parâmetros e calibração

Os parâmetros do modo autônomo ficam concentrados no topo do firmware e podem ser ajustados conforme o ambiente:

| Parâmetro | Valor atual | Descrição |
|---|---|---|
| `distanciaMaxima` | `25` (cm) | Distância mínima para considerar que há obstáculo à frente. |
| `correcaoMotorDireito` | `10.3` | Compensação de PWM no motor direito para corrigir o desvio de trajetória em linha reta. |
| Velocidade de movimento | `70.0` | PWM aplicado ao motor esquerdo (o direito recebe `velocidade - correcaoMotorDireito`). |
| Delay entre leituras | `30` ms | Intervalo entre as leituras dos sensores esquerdo e direito, evitando interferência entre os pulsos ultrassônicos. |
| Tempo de parada após detectar obstáculo | `1000` ms | Pausa antes de iniciar a manobra de desvio. |
| Tempo girando para a esquerda | `600` ms | Duração da manobra de desvio. |
| Timeout do `pulseIn` | `30000` µs | Tempo máximo aguardando o retorno do eco antes de considerar a leitura inválida (`999`). |

A calibração é empírica: ajusta-se `distanciaMaxima` conforme a velocidade do robô e o espaço necessário para frear, e `correcaoMotorDireito` conforme a tendência observada de o robô puxar para um dos lados.

## Limitações conhecidas

- **Desvio sempre para a esquerda:** o robô não escolhe o lado com mais espaço livre. Em corredores estreitos ou obstáculos posicionados à esquerda, pode tentar desviar repetidamente contra a parede.
- **Tempos fixos de manobra:** os `delay()` de parada (1 s) e giro (600 ms) bloqueiam o `loop()`. Durante a manobra, o robô não lê sensores nem responde a comandos via Wi-Fi.
- **Pontos cegos laterais e traseiros:** apenas dois sensores frontais são usados — obstáculos vindos de trás ou nas laterais não são detectados.
- **Superfícies problemáticas para o HC-SR04:** materiais macios, ângulos agudos ou superfícies muito refletivas podem produzir leituras incorretas ou retornar `999`, fazendo o robô tratar o caminho como livre.
- **Sem rampa de aceleração:** os motores partem direto na velocidade alvo, o que pode causar trancos em pisos com baixa aderência.
- **Sensibilidade à tensão da bateria:** como a velocidade é definida por PWM fixo, a velocidade real do robô cai conforme a bateria descarrega, alterando o espaço de frenagem efetivo sem que `distanciaMaxima` acompanhe.

