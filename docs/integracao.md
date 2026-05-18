# 🔄 Integração dos modos

O sistema opera com dois modos principais de forma independente:

- ✋ **Controle por gestos** (via webcam + Python)
- 🚙 **Modo autônomo** (desvio de obstáculos no ESP32)

A alternância entre os modos é controlada para evitar conflitos de comandos, garantindo que apenas um modo tenha controle ativo do robô por vez.

## 📡 Comunicação Python ↔ ESP32

A comunicação acontece por **HTTP sobre Wi-Fi**: o ESP32 sobe um servidor web (porta 80) na mesma rede local, e o script Python envia comandos via `GET` para a rota `/cmd`.

```
http://<IP_DO_ESP32>/cmd?action=<comando>
```

| Componente | Papel |
|---|---|
| ESP32 | Servidor HTTP (`WebServer` na porta 80), recebe comandos e controla os motores. |
| Python (`comunicacao.py`) | Cliente HTTP, envia `GET` com a ação detectada pela webcam. |
| Rede | Wi-Fi local — ambos precisam estar no mesmo SSID configurado no firmware. |

O Python usa `requests.get(..., timeout=0.1)` para que falhas de rede não travem o loop da webcam.

## 🎮 Comandos suportados

Os valores de `action` aceitos pela rota `/cmd` são:

| Comando | Efeito no robô |
|---|---|
| `frente` | Anda para a frente |
| `re` | Anda em ré |
| `direita` | Vira para a direita |
| `esquerda` | Vira para a esquerda |
| `parar` | Para os motores |
| `modo_gesto` | Entra em modo controle por gestos |
| `modo_auto` | Entra em modo autônomo (desvio) |

Comandos de movimento só têm efeito quando o ESP32 está em `modoAutomatico = false`. No modo autônomo, comandos de movimento são ignorados — apenas `modo_gesto` é processado para sair do modo.

## 🔁 Alternância entre modos

A troca é disparada pelo **gesto de "OL"** (ver `src/mocap/gestos.py`):

- Ao iniciar, o Python envia `modo_gesto` para garantir um estado conhecido.
- Cada detecção do gesto OL alterna entre `modo_gesto` e `modo_auto`.
- Um **cooldown de 3 segundos** (`cooldown_toggle = 3.0`) impede trocas acidentais por detecções consecutivas no mesmo gesto.

```
modoAutomatico = True
└── gesto OL detectado → envia "modo_gesto"  → entra em controle por gestos
    └── gesto OL detectado → envia "modo_auto" → volta ao modo autônomo
```

## 🛡️ Anti-spam de comandos

Para evitar sobrecarregar o ESP32 com requisições repetidas, o Python aplica um **cooldown de 100 ms** entre envios:

```python
if action is not None:
    if time.time() - last_send > 0.1:
        last_send = enviar_comando(action, last_send)
```

Combinado com o detector de gestos rodando uma única vez por frame (em vez de 21 vezes, uma por landmark), o fluxo de comandos passou a ser estável e previsível.

## ⏱️ Failsafe de timeout no ESP32

O ESP32 guarda o `millis()` do último comando recebido. No modo gestos, se passar mais de **1 segundo sem novos comandos** (`timeout = 1000`), o robô para automaticamente:

```cpp
if(millis() - ultimoComando > timeout && !modoAutomatico){
    parar();
}
```

Isso garante que uma queda de conexão, fechamento do script Python ou travamento da webcam não deixem o robô em movimento descontrolado.

## 🧪 Testes realizados

Durante o desenvolvimento foram realizados testes focados em:

- Estabilidade da comunicação entre Python e ESP32
- Resposta dos motores em comandos simultâneos
- Troca entre controle manual e automático
- Consistência dos movimentos em diferentes cenários
- Latência entre detecção de gesto e execução dos comandos

