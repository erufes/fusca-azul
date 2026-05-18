# 🚙 FUSCA AZUL  

## Robô com Controle por Gestos e Desvio Automático de Obstáculos  

Projeto dos trainees da Equipe de Robótica da UFES (ERUS) para desenvolvimento de um veículo com dois modos de operação:  

-  Controle por gestos (via webcam)  
-  Desvio automático de obstáculos  

## 🧩 Componentes Utilizados

- ESP32 - HW-394
- Sensor ultrassônico - HC-SR04
- Ponte H - L298N

## 📚 Documentação

A documentação detalhada do projeto está organizada na pasta [`docs/`](./docs):

- ✋ [**Controle por Gestos**](./docs/mocap.md) — reconhecimento de gestos via webcam com Python, OpenCV e MediaPipe.
- 🚧 [**Desvio de Obstáculos**](./docs/desvio_de_obstaculos.md) — modo autônomo no ESP32 com sensores ultrassônicos.
- 🔄 [**Integração dos Modos**](./docs/integracao.md) — comunicação Python ↔ ESP32, protocolo HTTP e alternância de modos.

## 🚧 Status do Projeto  

✔️ Protótipo funcional completo  

O sistema encontra-se em estágio de **protótipo funcional**, com ambos os modos (controle por gestos e desvio automático de obstáculos) já implementados e operando corretamente. Atualmente, estão sendo realizados apenas ajustes finais de acabamento e melhorias estéticas.

## 👥 Equipe  

- Yágo Amorim  
- Pietro Pazini  
- Dimitry Deveza  
- Daniel Rodrigues  
- Pedro Vairo
