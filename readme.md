# 🚙 FUSCA AZUL  

## Robô com Controle por Gestos e Desvio Automático de Obstáculos  

Projeto dos trainees da Equipe de Robótica da UFES (ERUS) para desenvolvimento de um veículo com dois modos de operação:  

-  Controle por gestos (via webcam)  
-  Desvio automático de obstáculos  

##  Descrição  

O robô será controlado por um ESP32 e terá dois modos:  

### ✋ Controle por gestos 

Projeto desenvolvido utilizando Python, [OpenCV](https://opencv.org) e [MediaPipe](https://mediapipe.dev) para reconhecer gestos em tempo real por uma webcam, o que transforma movimentos das mãos em comandos por via do ESP32.

#### 🚀 Otimização

Esta parte do projeto teve focou em otimizar a performance, estabilidade do reconhecimento e o fluxo de comandos.

#### ⚡ Problemas Encontrados

- A detecção de gestos estava sendo executada 21 vezes por frame, o que poderia sobrecarregar o computador.
- O sistema enviava comandos continuamente, gerando spam.
- O terminal recebia múltiplos prints repetidos.
- Havia instabilidade quando nenhuma mão era detectada, podendo crashar o programa.

#### ✅ Otimizações Implementadas

##### Correção do processamento excessivo

A lógica de reconhecimento de gestos foi removida do loop de landmarks. Porque, como o MediaPipe tem 21 landmarks por mão, o programa fazia verificação 21 vezes por frame, causando sobrecargarregando e gerando spam de comandos.

Agora os landmarks são apenas para renderização visual, enquanto os gestos são detectados apenas uma vez por frame.

---

##### Sistema anti-spam de comandos

Foi criado um sistema de cooldown utilizando timestamps para impedir o envio contínuo de comandos.

```python
if time.time() - last_send > 0.1:
    last_send = enviar_comando(action, last_send)
if time.time() - last_send > 0.1:
    last_send = enviar_comando(action, last_send) 
```
#### 📈 Resultados Obtidos
Redução significativa do uso de CPU
Eliminação de spam de comandos
Reconhecimento mais estável
Melhor organização do fluxo do programa
Comunicação mais eficiente

#### ✋ Gestos Implementados

Gesto:	    Ação:
frente()	  Movimento para frente
re()	      Movimento reverso
direita()	  Movimento para direita
esquerda()	Movimento para esquerda
parado()	  Para o movimento

#### ▶️ Execução

##### 1. Clone o repositório

```bash
git clone <url-do-repositorio>
```

##### 2. Instale as dependências

```bash
pip install opencv-python mediapipe
```

##### 3. Execute o projeto

```bash
python main.py
```
### 🚧 Desvio de obstáculos  

Modo autônomo usando sensor ultrassônico para detectar e evitar colisões.  

Tecnologias previstas:  

- ESP-32D
- Sensor ultrassônico (HC - SR04)
- Ponte H

##  Status do Projeto:  

🚧 Em desenvolvimento (fase inicial)  

## 👥 Equipe  

Yágo Amorim  
Pietro Pazini  
Dimitry Deveza  
Daniel Rodrigues  
Pedro Vairo
