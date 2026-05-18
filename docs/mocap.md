# ✋ Controle por Gestos

Modo desenvolvido utilizando Python, [OpenCV](https://opencv.org) e [MediaPipe](https://mediapipe.dev) para reconhecer gestos em tempo real por uma webcam, o que transforma movimentos das mãos em comandos para o ESP32.

## ✋ Gestos suportados

| Gesto | Ação |
|---|---|
| `frente()` | Robô anda pra frente |
| `re()` | Robô da Rê |
| `direita()` | Robô vai para direita |
| `esquerda()` | Robô vai para a esquerda |
| `parado()` | Para o Robô |

## ⚡ Problemas encontrados e ✅ Otimizações

### ⚡ Problemas encontrados

- A detecção de gestos estava sendo executada 21 vezes por frame, o que poderia sobrecarregar o computador.
- O sistema enviava comandos continuamente, gerando spam.
- O terminal recebia múltiplos prints repetidos.
- Havia instabilidade quando nenhuma mão era detectada, podendo crashar o programa.

#### ✅ Otimizações Implementadas

##### Correção do processamento excessivo

A lógica de reconhecimento de gestos foi removida do loop de landmarks. Porque, como o MediaPipe tem 21 landmarks por mão, o programa fazia verificação 21 vezes por frame, causando sobrecargarregando e gerando spam de comandos.

Agora os landmarks são apenas para renderização visual, enquanto os gestos são detectados apenas uma vez por frame.

##### Sistema anti-spam de comandos

Foi criado um sistema de cooldown utilizando timestamps para impedir o envio contínuo de comandos.

```python
if time.time() - last_send > 0.1:
    last_send = enviar_comando(action, last_send)
if time.time() - last_send > 0.1:
    last_send = enviar_comando(action, last_send) 
```
#### 📈 Resultados Obtidos

- Redução significativa do uso de CPU
- Eliminação de spam de comandos
- Reconhecimento mais estável
- Melhor organização do fluxo do programa
- Comunicação mais eficiente

#### ▶️ Instalação

##### 1. Clone o repositório

```bash
git clone https://github.com/erufes/fusca-azul.git
```

##### 2. Abra o terminal na pasta `src/mocap`

##### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

##### 4. Execute o projeto

```bash
python main.py
```
