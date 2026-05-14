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

| Gesto | Ação |
|---|---|
| `frente()` | Robô anda pra frente |
| `re()` | Robô da Rê |
| `direita()` | Robô vai para direita |
| `esquerda()` | Robô vai para a esquerda |
| `parado()` | Para o Robô |
#### ▶️ Execução

##### 1. Clone o repositório

```bash
git clone https://github.com/erufes/fusca-azul.git
```

##### 2. Instale as dependências

```bash
pip install opencv-python mediapipe
```

##### 3. Abra o terminal na pasta `mocap`

##### 4. Execute o projeto

```bash
python main.py
```
## 🚧 Desvio de obstáculos  

Modo autônomo usando sensor ultrassônico para detectar e evitar colisões.  

Tecnologias previstas:  

- ESP-32D  
- Sensor ultrassônico (HC-SR04)  
- Ponte H  

### 🧪 Testes realizados com sensores  

Durante o desenvolvimento, foram realizados testes com diferentes configurações de sensores para avaliar a melhor estratégia de detecção de obstáculos:  

- 🔹 **1 sensor:** funcionamento simples e direto, porém com limitação na detecção lateral, reduzindo a precisão dos desvios.  
- 🔹 **2 sensores:** melhor equilíbrio entre custo, complexidade e eficiência, permitindo detecção mais confiável e decisões de desvio mais estáveis.  
- 🔹 **3 sensores:** maior cobertura de detecção, porém com aumento da complexidade de leitura e necessidade de maior calibração do sistema.  

### 📌 Conclusão dos testes  

A configuração com **2 sensores frontais apresentou o melhor custo-benefício**, sendo a solução mais estável e eficiente para o comportamento de desvio automático do robô.  

---

## 🔄 Integração dos modos  

O sistema foi projetado para operar com dois modos principais de forma independente:  

- ✋ Controle por gestos (via webcam + Python)  
- 🚙 Modo autônomo (desvio de obstáculos no ESP32)  

A alternância entre os modos é feita de forma controlada para evitar conflitos de comandos, garantindo que apenas um modo tenha controle ativo do robô por vez.  

### 🧪 Testes realizados  

Durante o desenvolvimento foram realizados testes focados em:  

- Estabilidade da comunicação entre Python e ESP32  
- Resposta dos motores em comandos simultâneos  
- Troca entre controle manual e automático  
- Consistência dos movimentos em diferentes cenários  
- Latência entre detecção de gesto e execução dos comandos  

Também foi implementado um sistema de **anti-spam de comandos**, reduzindo envios repetidos e melhorando a estabilidade geral do controle por gestos.  

---

## 🚧 Status do Projeto  

✔️ Protótipo funcional completo  

O sistema encontra-se em estágio de **protótipo funcional**, com ambos os modos (controle por gestos e desvio automático de obstáculos) já implementados e operando corretamente. Atualmente, estão sendo realizados apenas ajustes finais de acabamento e melhorias estéticas.

## 👥 Equipe  

Yágo Amorim  
Pietro Pazini  
Dimitry Deveza  
Daniel Rodrigues  
Pedro Vairo
