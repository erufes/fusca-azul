# ESP32-CAM e navegação visual

A ESP32-CAM **AI Thinker com OV2640 e PSRAM** é opcional e coexiste com o
NodeMCU/ESP8266. Sem ela, o controle por gestos continua funcionando.

```text
ESP32-CAM → JPEG por Wi-Fi → computador → comandos TCP → ESP8266 → L298N
                                 ↓
                     vídeo + mapa de profundidade
```

A câmera não comanda os motores. O computador executa o modelo MiDaS v2.1
small para estimar profundidade relativa e escolhe frente, esquerda, direita
ou parar. Não há marcha à ré autônoma, pois a câmera não vê atrás do robô.

## Instalar e gravar

Na raiz do projeto:

```bash
uv sync
pio run -e nodemcuv2 -e esp32cam
pio run -e nodemcuv2 --target upload --upload-port PORTA_DO_ESP8266
pio run -e esp32cam --target upload --upload-port PORTA_DA_ESP32CAM
uv run gestos
```

Substitua as portas pelas de cada placa. O ambiente padrão continua sendo
`nodemcuv2`: um `pio run --target upload` sem `-e` não grava a câmera.

A ESP32-CAM precisa de alimentação estável e suficiente pelo pino **5V**;
não a alimente pela saída 3V3 do ESP8266. Use sinais seriais de 3,3 V para gravar.
Na placa sem gravador integrado, ligue GPIO0 ao GND durante a gravação e
remova essa ligação antes de reiniciar. Monte a câmera sem espelhamento,
com a imagem na orientação correta, voltada para a frente e inclinada para
que o piso apareça na metade inferior. Não há ligação de dados entre as placas.

## Wi-Fi da câmera

Configure cada placa na mesma rede Wi-Fi de 2,4 GHz do computador.
A ESP32-CAM tenta a última rede salva por 20 segundos. Sem conexão, abre
`fusca-cam-<identificador>`; conecte-se ao hotspot e abra **http://192.168.4.1**.
Informe nome e senha. Só após obter conexão/IP as credenciais substituem a
configuração anterior em NVS; então a câmera reinicia. Senha errada mantém
a configuração anterior. Ao perder a rede, tenta reconectar e volta ao portal.

O hotspot é aberto e temporário, para configuração por proximidade. O vídeo
usa HTTP local, sem autenticação ou criptografia; use uma rede confiável.
A câmera anuncia `_fusca-cam._tcp.local.` na porta 80. A ESP8266 continua
procurando `_fusca-azul._tcp.local.` para encontrar o servidor de comandos.
São serviços diferentes e não competem entre si.

## Usar no aplicativo

1. Abra a aba **Robô · ESP32-CAM**.
2. Deixe o endereço vazio para descoberta por mDNS e clique em **Conectar
   ESP32-CAM**. Se houver várias câmeras ou multicast bloqueado, informe
   `http://IP-DA-CAMERA/capture`. O endereço digitado é lembrado entre sessões.
3. Na primeira conexão, o aplicativo baixa o modelo de profundidade. Aguarde
   o carregamento. A webcam de gestos não é necessária para operar pelos botões.
4. Confira a imagem e o mapa de profundidade. Áreas vermelhas indicam possível
   obstáculo ou ausência de piso; as três faixas indicam as regiões analisadas.
   No mapa, cores mais claras representam maior proximidade relativa.
5. Com **Robô conectado** e análise recente/válida, clique em **Iniciar
   automático**. Antes disso, a transmissão é apenas uma prévia e não move motores.
6. Use **Parar robô / sair do automático** para interromper. Isso também pausa
   a captura de gestos para que o próximo gesto não reinicie os motores.

O gesto de rock também pode entrar no modo automático, desde que a transmissão
esteja conectada e pronta. Sem câmera pronta, o modo automático não é ativado.
Ao sair, a webcam é pausada; use **Ativar câmera** para retomar controle manual.
Pausar/trocar a webcam durante o modo automático também interrompe o movimento.
Após desconexão ou atraso, o modo não se reativa sozinho.

## Baixar o modelo de profundidade

O [modelo ONNX oficial MiDaS v2.1 small](https://github.com/isl-org/MiDaS/releases/download/v2_1/model-small.onnx)
é diferente do modelo de reconhecimento de gestos. Use o arquivo **model-small.onnx**
desse link, não os arquivos `.pt` ou `.pb`.

### Download automático

Com acesso à internet, abra `uv run gestos`, entre na aba **Robô · ESP32-CAM**
e clique em **Conectar ESP32-CAM**. Depois de localizar a câmera, o aplicativo
baixa o modelo se ele ainda não existir. Aguarde a mensagem de preparação;
o download só é necessário na primeira vez.

O arquivo fica em `fusca-azul/midas-v21-small.onnx` dentro do cache do usuário:

- Linux: `$XDG_CACHE_HOME`, ou `~/.cache` quando essa variável não está definida.
- macOS: `~/Library/Caches`.
- Windows: `%LOCALAPPDATA%`.

### Download manual no Linux ou macOS

Execute na raiz do projeto. Esta opção permite preparar o modelo antes de
conectar a câmera:

```bash
mkdir -p src/gestos/model
curl --fail --location --retry 3 \
  --output src/gestos/model/midas-v21-small.onnx \
  https://github.com/isl-org/MiDaS/releases/download/v2_1/model-small.onnx
```

Após o download terminar com sucesso, inicie o aplicativo indicando o arquivo:

```bash
FUSCA_DEPTH_MODEL="$PWD/src/gestos/model/midas-v21-small.onnx" uv run gestos
```

### Download manual no Windows (PowerShell)

Execute na raiz do projeto:

```powershell
New-Item -ItemType Directory -Force -Path "src/gestos/model" | Out-Null
Invoke-WebRequest `
  -Uri "https://github.com/isl-org/MiDaS/releases/download/v2_1/model-small.onnx" `
  -OutFile "src/gestos/model/midas-v21-small.onnx" `
  -ErrorAction Stop
```

Após o download terminar com sucesso:

```powershell
$env:FUSCA_DEPTH_MODEL = (Resolve-Path "src/gestos/model/midas-v21-small.onnx").Path
uv run gestos
```

### Conferir o arquivo e usar sem internet

Para conferir se o OpenCV consegue carregar o arquivo baixado manualmente,
execute na raiz do projeto, em qualquer um dos sistemas:

```bash
uv run python -c "import cv2; cv2.dnn.readNetFromONNX('src/gestos/model/midas-v21-small.onnx'); print('Modelo carregado com sucesso')"
```

Essa verificação confirma o carregamento, não a qualidade das previsões.
Se o download for interrompido ou o arquivo não carregar, repita o download
antes de iniciar a navegação. O diretório `src/gestos/model` já é ignorado pelo Git.

Para usar outro local, ajuste `FUSCA_DEPTH_MODEL` para o caminho do arquivo.
Quando essa variável está definida, o aplicativo usa somente o arquivo indicado
e não tenta baixá-lo automaticamente. No Linux/macOS, repita a variável a cada
execução; no PowerShell, ela vale para a sessão atual. Com as dependências e o
modelo já instalados, a análise funciona sem internet, usando apenas a rede local.

## Funcionamento da análise

Use exatamente esse export ONNX (entrada RGB 256 × 256 entre 0 e 1, com
normalização incorporada ao modelo). A inferência usa OpenCV DNN em CPU;
não requer PyTorch, serviço em nuvem ou transmissão de vídeo para a internet.
O código segue o [pré-processamento oficial](https://github.com/isl-org/MiDaS/blob/master/tf/run_onnx.py).

A análise ajusta um plano de piso à profundidade inversa da metade inferior
da imagem. Superfícies inesperadamente próximas, ou ausência do piso esperado,
marcam regiões bloqueadas. Sem plano confiável, com imagem muito escura,
superexposta ou profundidade inválida, o resultado é parar.

- Caminho central livre por três imagens consecutivas: frente.
- Centro bloqueado e um lado livre: curva para esse lado.
- Obstáculo na região próxima, ambos os lados bloqueados ou incerteza: parar.
- Curvas são limitadas a pulsos de aproximadamente 350 ms, intercalados com
  pausas de 250 ms para reavaliar. Esses tempos dependem da frequência dos quadros.

A imagem é obtida por consultas JPEG a `/capture`, com resolução 320 × 240.
O firmware descarta a exposição enfileirada antes de atender a consulta e envia
identificador crescente e idade da imagem em `X-Fusca-Frame` e
`X-Fusca-Age-Ms`. Não é um endpoint MJPEG genérico: use o firmware deste projeto.
O aplicativo mantém somente o resultado mais recente, sem fila de vídeo.

Captura, transferência e inferência precisam caber em **400 ms** para habilitar
autonomia. O relógio do comando preserva o instante anterior à transferência;
um quadro atrasado não ganha validade nova ao chegar à interface. Falta de
atualização, desconexão do robô ou fechamento interrompem o automático.
O watchdog de comunicação do ESP8266 continua funcionando independentemente.

## Limites e validação na montagem real

Esta é uma implementação experimental de navegação monocular, não um sistema
com distância métrica ou garantia de prevenção de colisões. A profundidade é
relativa e o indicador de análise válida vem de verificações geométricas;
não é uma probabilidade de acerto do modelo. Pisos variados são processados
pelo modelo aprendido, mas mudanças extremas de luz, vidro, objetos finos,
objetos fora do campo de visão, escadas, superfícies sem textura e piso muito
inclinado podem gerar falhas. A largura das faixas não foi calibrada para a
largura física do robô nem para sua distância de frenagem.

O ESP8266 mantém os motores em velocidade total quando recebe movimento.
A parada desabilita a ponte, sem frenagem ativa. Para uso além dos testes
supervisionados, acrescente sensores de distância e parada física e calibre
velocidade, montagem, campo de visão e limiares em `src/gestos/autonomy.py`.
Não teste esta versão perto de escadas ou bordas.

Primeiro teste com rodas suspensas. Depois, em área controlada, verifique:
obstáculo no centro, lados e região próxima; ausência de piso; iluminação;
perda de Wi-Fi; desligamento da câmera; suspensão do aplicativo; fechamento
da janela; e troca entre modos. Confirme os sentidos esquerdo/direito da
câmera e dos motores. Os testes sintéticos não validam o desempenho do MiDaS
nem a segurança de movimento em um ambiente real.

## Diagnóstico

- Permita HTTP TCP 80 da câmera, TCP 8765 do servidor e mDNS UDP 5353.
- Se a análise ultrapassar 400 ms, o vídeo pode aparecer como prévia, mas o
  automático fica indisponível. Aproxime o roteador e use um computador mais rápido.
- Se houver erro ao carregar o ONNX, confira o arquivo e a versão do OpenCV;
  nenhuma regra de navegação por cor é usada como substituição silenciosa.
- Se houver `No module named intelhex` ao compilar, use a instalação completa
  do PlatformIO. Neste computador foi validado
  `/home/ddeveza/.platformio/penv/bin/pio run -e esp32cam`.
- Logs da placa: `pio device monitor -e esp32cam` a 115200 baud.
- Testes: `uv run python -m unittest discover -s tests -v`.

Referência de hardware: [pinagem AI Thinker da Espressif](https://github.com/espressif/arduino-esp32/blob/master/libraries/ESP32/examples/Camera/CameraWebServer/camera_pins.h).
