# 🤖 Fusca-Azul — Controle de Robô por Gestos

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10%2B-00C853?style=for-the-badge&logo=google&logoColor=white)
![ESP32](https://img.shields.io/badge/ESP32-IoT-E7352C?style=for-the-badge&logo=espressif&logoColor=white)

> Controle um carrinho robô em tempo real usando apenas gestos da mão — capturados pela webcam, interpretados com IA e transmitidos via Wi-Fi para um ESP32.

---

## 🎯 Sobre o Projeto

O **mocap** é um sistema de controle gestual para um carrinho robô físico. A câmera do computador captura os movimentos da mão do usuário, o MediaPipe detecta os 21 pontos de referência (landmarks) da mão em tempo real, e um algoritmo converte configurações de dedos em comandos de direção. Os comandos são enviados via HTTP para um ESP32 embarcado no carrinho, que controla os motores.

O sistema conta com dois modos de operação:
- **Modo Gesto:** o usuário dirige o carrinho manualmente com a mão
- **Modo Automático:** o carrinho opera de forma autônoma (controlado pelo ESP32)

A troca entre os modos é feita com um gesto especial — o "L" (polegar + indicador levantados).

---

## 🚀 Funcionalidades

| Gesto            | Configuração dos Dedos    | Comando                  |
|------------------|---------------------------|--------------------------|
| ✋ Mão aberta    | Todos os dedos levantados | Frente                   |
| ✊ Punho fechado | Nenhum dedo levantado     | Parar                    |
| ✌️ V de vitória  | Indicador + Médio         | Ré                       |
| 🤙 Mindinho      | Apenas mindinho levantado | Direita                  |
| 👍 Polegar       | Apenas polegar levantado  | Esquerda                 |
| 👆 L             | Polegar + Indicador       | Alternar modo Auto/Gesto |

- 📷 **Detecção de mão em tempo real** via webcam com MediaPipe
- 🧠 **Reconhecimento gestual robusto** baseado em geometria de landmarks (sem ML treinado)
- 📡 **Comunicação Wi-Fi** com ESP32 via requisições HTTP leves
- 🔁 **Troca de modo com cooldown** para evitar acionamentos acidentais
- ⚡ **Throttling de comandos** (mínimo 100ms entre envios) para não sobrecarregar o ESP32
- 🖼️ **Preview ao vivo** com landmarks desenhados sobre o feed da câmera

---

## 🛠 Tecnologias

- **[Python 3.10+](https://www.python.org/)** — linguagem principal
- **[OpenCV](https://opencv.org/)** — captura e exibição do feed da câmera
- **[MediaPipe](https://mediapipe.dev/)** — detecção e rastreamento de landmarks da mão
- **[Requests](https://requests.readthedocs.io/)** — envio de comandos HTTP ao ESP32
- **[ESP32](https://www.espressif.com/en/products/socs/esp32)** — microcontrolador embarcado no carrinho (firmware separado)

---

## 📦 Instalação

### Pré-requisitos

- Python 3.10 ou superior
- Webcam conectada ao computador
- ESP32 no mesmo segmento de rede Wi-Fi
- Pip atualizado

### 1. Clone o repositório

```bash
git clone https://github.com/erufes/fusca-azul.git
cd src/mocap
```

### 2. Crie e ative um ambiente virtual (recomendado)

```bash
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Instale as dependências

```bash
pip install -r requirements.txt
```

### 4. Baixe o modelo do MediaPipe

```bash
mkdir -p utils
curl -L https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task \
  -o utils/hand_landmarker.task
```

### 5. Configure o IP do ESP32

Abra o arquivo `requisicoes.py` e confira o IP:

```python
ESP32_IP = "192.168.0.50"  # ← IP padrão do nosso ESP32
```

> 💡 Você pode encontrar o IP do ESP32 pelo monitor serial da Arduino IDE ou pelo painel do seu roteador.

---

## ▶️ Como Executar

```bash
python main.py
```

Uma janela chamada **"Feed"** será aberta mostrando o vídeo da câmera com os landmarks da mão desenhados em tempo real. Feche a janela para encerrar o programa.

---

## 📁 Estrutura do Projeto

```
mocap/
│
├── main.py            # Loop principal: captura, detecção e envio
├── gestos.py          # Classe Gestos — interpreta configurações de dedos
├── dedos.py           # Funções auxiliares de geometria dos landmarks
├── requisicoes.py     # Comunicação HTTP com o ESP32
│
├── utils/
│   └── hand_landmarker.task   # Modelo MediaPipe (baixado separadamente)
│
├── requirements.txt   # Dependências Python
└── README.md
```

### Responsabilidade de cada módulo

| Arquivo          | Descrição                                                                 |
|------------------|---------------------------------------------------------------------------|
| `main.py`        | Inicializa a câmera, o modelo e o event loop principal                    |
| `dedos.py`       | Calcula se cada dedo está levantado com base na distância entre landmarks |
| `gestos.py`      | Converte o estado dos dedos em gestos nomeados                            |
| `requisicoes.py` | Envia requisições GET ao endpoint `/cmd?action=` do ESP32                 |

---

## 📌 Exemplo de Uso

```
# Com o programa rodando e a câmera ativa:

# 1. Levante todos os dedos → carrinho vai para frente
# 2. Feche o punho → carrinho para
# 3. Levante indicador e médio (V) → carrinho recua
# 4. Levante apenas o mindinho → vira à direita
# 5. Levante apenas o polegar  → vira à esquerda
# 6. Faça o "L" (polegar + indicador) por 3 segundos → ativa modo automático
# 7. Repita o "L" → volta ao modo gesto
```

### Endpoint do ESP32

O carrinho espera requisições no seguinte formato:

```
GET http://<IP_ESP32>/cmd?action=<comando>
```

Comandos suportados: `frente`, `re`, `parar`, `direita`, `esquerda`, `modo_auto`, `modo_gesto`

---

## 👨‍💻 Autor

Feito com ☕ por

**Daniel Rodrigues e Pedro Vairo**

[![GitHub](https://img.shields.io/badge/GitHub-Daniel_Rodrigues-181717?style=flat-square&logo=github)](https://github.com/dhex9)
[![GitHub](https://img.shields.io/badge/GitHub-Pedro_Vairo-181717?style=flat-square&logo=github)](https://github.com/Kahooty388)