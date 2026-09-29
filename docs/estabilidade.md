# Correção de rumo com GY-80

O firmware usa o giroscópio L3G4200D do GY-80 para compensar diferenças entre
os motores em frente e ré. `Gy80` lê e calibra o sensor; `HeadingControl`
calcula a correção; `Robot` aplica o PWM e mantém as condições de parada.
Não usa bússola, acelerômetro ou barômetro nesta versão.

## Ligação e montagem

| GY-80 | NodeMCU |
| --- | --- |
| SDA | D7 / GPIO13 |
| SCL | D8 / GPIO15 |
| GND | GND comum |

Use alimentação apropriada ao módulo e pull-ups de SDA/SCL para **3,3 V**,
nunca 5 V nos GPIOs da ESP. Monte rigidamente, com o eixo
**+X do giroscópio apontando para cima**, conforme a montagem atual. O sinal esperado é positivo ao girar o robô para
esquerda, visto de cima. Se montado invertido, altere `YAW_SIGN` em `Gy80.cpp`
para `-1`. Para outra orientação, selecione `YAW_AXIS` no driver (X=0, Y=1, Z=2).

**D8 exige atenção:** GPIO15 precisa estar baixo no reset para a ESP iniciar
pela flash. O pull-up do SCL pode impedir o boot. Isso não pode ser corrigido
pelo firmware, que ainda não começou a executar. Se ocorrer, mova SCL para
D6 e altere `gyro.begin(D7, D8)` para `gyro.begin(D7, D6)` em `main.cpp`.
Veja a [documentação de boot da Espressif](https://docs.espressif.com/projects/esptool/en/latest/esp8266/advanced-topics/boot-mode-selection.html).

A correção pressupõe que frente, ré e os lados dos motores já correspondem
à montagem física. Ela não corrige saídas cruzadas na ponte ou um motor invertido.

## Inicialização e falhas

Deixe o robô totalmente imóvel durante o boot. O driver procura a identidade
`0xD3` em `0x68` e `0x69`, configura 100 Hz / ±250 graus/s e coleta 200 amostras
para estimar o offset, após 250 ms de aquecimento. Normalmente leva cerca de
3 segundos. A dispersão dos três eixos rejeita movimento evidente; rotação
lenta constante pode passar pelo teste, portanto mantenha-o imóvel.

Os motores ficam desabilitados até `[GY80] ... -> PRONTO`. Sensor ausente,
erro I2C, saturação ou leitura atrasada mais de 100 ms durante movimento
param o robô e bloqueiam comandos. Falha é mantida até reiniciar; corrija a
ligação ou imobilize o robô antes de reiniciar. A calibração falha após 10 s
se não obtiver amostras estáveis. Pausas da descoberta de rede enquanto parado
não são integradas como movimento. Comandos ausentes por 400 ms também param.

## Controle e ajuste

Ao iniciar frente ou ré, o rumo atual vira a referência. O controlador integra
a velocidade angular X para estimar o desvio relativo e aplica uma correção
proporcional ao desvio mais amortecimento pela velocidade angular. Comandos
repetidos preservam a referência. Parar, inverter o movimento ou fazer curva
reinicia essa referência. Curvas manuais não recebem correção de rumo.

Os dois motores começam em 512/1024 (50%). A correção só reduz um deles, até
358/1024 (aproximadamente 35%); não aumenta nenhum acima de 50% e não inverte
um motor para compensar. Na ré, a seleção da roda a reduzir é invertida.

`HeadingControl.h` contém os valores iniciais, ainda sujeitos a ajuste físico:

- ganho de desvio: 8 unidades PWM por grau;
- ganho de velocidade angular: 2 unidades PWM por grau/s;
- redução máxima: 154 unidades PWM;
- desvio integrado limitado a ±30 graus.

Teste primeiro com rodas suspensas para verificar pinagem, sentidos e paradas.
Depois teste trechos curtos em piso livre, começando parado. Se a correção
acentuar a curva, pare e confira a orientação do sensor e os lados dos motores.
Se oscilar, reduza os ganhos antes de testar novamente. A calibração e os ganhos
precisam ser validados na placa; a simulação não mede aderência, corrente ou carga.
O giroscópio acumula deriva ao longo do tempo: isto é manutenção de rumo relativo
em trechos, não navegação absoluta ou controle de velocidade por encoders.

Logs `[GY80]`, `[RUMO]` e `[ROBO]` aparecem no monitor serial a 115200 baud.
O teste `tests/test_firmware.py` compila uma simulação C++ com `g++`, quando
disponível, e verifica calibração, falhas, teto do PWM, frente/ré, comandos
repetidos e compensação de um motor 10% mais forte.

Registradores e escala seguem o [datasheet ST L3G4200D, revisão 3](https://cdn.sparkfun.com/datasheets/Sensors/Gyros/3-Axis/CD00265057.pdf).
