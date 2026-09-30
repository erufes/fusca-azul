# Fusca Azul

Nova versão do robô Fusca Azul, da ERUS/UFES. O software e o hardware estão
em atualização. O reconhecimento de gestos agora usa um aplicativo desktop
em Qt, com servidor local de comandos e configuração do Wi-Fi do robô pelo navegador.

## Executar

Requer Python 3.14 ou superior, [uv](https://docs.astral.sh/uv/) e uma webcam.
Na raiz do projeto:

```bash
uv run gestos
```

No Ubuntu, Debian ou Linux Mint, instale também a biblioteca de cursor usada
pelo Qt no X11:

```bash
sudo apt-get install libxcb-cursor0
```

O uv instala as dependências e abre a janela. Na primeira execução, o aplicativo
baixa o modelo do MediaPipe, caso ele ainda não esteja disponível. As próximas
execuções podem funcionar sem internet, com as dependências e o modelo instalados.
Permita o acesso à câmera nas configurações de privacidade do sistema, se necessário.

A interface mostra a câmera espelhada, os pontos da mão, o gesto reconhecido e o
modo selecionado. Para usar outra webcam, abra a engrenagem no canto superior direito,
selecione a câmera pelo nome e clique em **Aplicar**. Se a captura estiver ativa,
o aplicativo troca a câmera automaticamente. Use **Atualizar lista** depois
de conectar ou desconectar uma webcam.

Python, Qt e MediaPipe têm versões para Linux, Windows e macOS, mas a combinação
de versões e arquitetura precisa ser compatível. No Linux, o Qt pode exigir
bibliotecas gráficas do sistema. Não há empacotamento nem Docker.

**Os gestos controlam o robô por Wi-Fi.** O aplicativo anuncia o servidor por
mDNS, e o robô o encontra automaticamente. Com a ESP32-CAM opcional, o modo Automático analisa profundidade no computador
para avançar, desviar ou parar. O vídeo e o mapa de profundidade aparecem no
aplicativo. Veja [ESP32-CAM e navegação visual](docs/espcam.md) para instalação,
uso e limites desta implementação experimental.

Veja [configuração de Wi-Fi e protocolo](docs/comunicacao.md) para conectar o robô.

## Firmware do robô

O NodeMCU/ESP8266 controla dois motores pela ponte H L298N, com correção de rumo pelo GY-80.
O robô inicia parado e recebe frente, ré, esquerda, direita e parar da aplicação.
Sem comandos recentes ou conexão, volta a parar. As curvas giram as rodas em
sentidos opostos. Os motores operam com PWM de até 50% nos pinos ENA/ENB; a parada desabilita
os canais e deixa os motores desacelerarem livremente.

| L298N | NodeMCU |
| --- | --- |
| ENA | D0 |
| IN1 | D2 |
| IN2 | D1 |
| IN3 | D3 |
| IN4 | D4 |
| ENB | D5 |

Remova os jumpers de ENA e ENB para conectar os sinais do NodeMCU. Ligue o
motor esquerdo em OUT1/OUT2 e o direito em OUT3/OUT4. Use alimentação adequada
para os motores na ponte e conecte o GND da ponte ao GND do NodeMCU.
Remova qualquer ligação antiga de sensor em D1 e D2: esses pinos controlam a ponte.
O GY-80 usa SDA em **D7 (GPIO13)** e SCL em **D8 (GPIO15)**, com GND comum
e níveis de sinal de 3,3 V. Veja [montagem, calibração e ajuste de rumo](docs/estabilidade.md).
D3 e D4 precisam permanecer em nível alto durante o boot do ESP8266;
a ligação externa não deve forçá-los a nível baixo durante a inicialização.

Se uma roda girar no sentido contrário ao esperado, troque os dois fios desse
motor nas saídas da ponte, com a alimentação desligada.

A classe `Motor` abstrai cada canal da L298N, e a classe `Robot` coordena os dois
motores. Os pinos e a composição dos módulos ficam em `src/firmware/main.cpp`.
`WifiConnection` cuida do Wi-Fi e do portal, `WifiCredentials` da persistência
e `GestosConnection` da descoberta mDNS e do protocolo de comandos.
`Robot` registra as mudanças de movimento no monitor serial (115200 baud).

Para compilar e gravar com PlatformIO:

```bash
pio run
pio run --target upload
```

## Organização

- `src/gestos/application.py`: inicialização do aplicativo e logs.
- `src/gestos/ui/`: janela, visualização do vídeo e tema.
- `src/gestos/network.py`: servidor TCP, validade dos comandos e anúncio mDNS.
- `src/gestos/devices.py`: descoberta das câmeras pelo nome.
- `src/gestos/camera.py`: captura e processamento em uma thread separada.
- `src/gestos/detection.py`: integração com MediaPipe e sessão de reconhecimento.
- `src/gestos/recognition.py`: geometria e classificação dos gestos.
- `src/gestos/modes.py`: regras de troca de modo.
- `src/gestos/model.py`: localização e download do modelo.
- `src/firmware/`: firmware PlatformIO para NodeMCU/ESP8266 e ponte H L298N.
- `src/espcam/`: firmware da ESP32-CAM AI Thinker, Wi-Fi e imagens JPEG.
- `src/gestos/espcam.py`: descoberta e recepção das imagens.
- `src/gestos/depth.py` e `src/gestos/autonomy.py`: profundidade MiDaS e decisões de navegação.
- [docs/gestos.md](docs/gestos.md): uso, gestos, modelo e logs.
- `tests/`: testes de reconhecimento, captura e interface.

A indentação usa tabs, conforme o `.editorconfig`.

Ao atualizar um ambiente da versão web, se o OpenCV apresentar erro ao abrir a
câmera, reinstale a única variante mantida pelo aplicativo. A versão anterior
instalava duas variantes que compartilhavam arquivos:

```bash
uv sync --reinstall-package opencv-contrib-python-headless
```

O projeto usa somente `opencv-contrib-python-headless`. A configuração do uv
exclui as variantes gráficas, inclusive a dependência transitiva do MediaPipe,
para evitar arquivos `cv2` sobrepostos e conflitos com os plugins do PySide6.

## Testes

```bash
uv run python -m unittest discover -s tests -v
```

Os testes da janela usam a plataforma Qt `offscreen` e câmeras simuladas;
não precisam de webcam nem do download do modelo. O uso real da câmera deve
ser verificado no computador que executa o aplicativo.

## Versão anterior

O código, a documentação, a placa e os modelos 3D antigos estão preservados no
histórico do Git, na tag anotada **v1.0.0**. Ela aponta para o
commit `7e1b7a9f1c05d8ae50a9d219d5c3933cf5e62812` da branch main, anterior à reescrita.
Não há uma cópia do legado na estrutura atual.

Para consultar um arquivo antigo sem alterar seu trabalho:

```bash
git show v1.0.0:README.md
```

Para abrir a versão antiga em uma pasta separada:

```bash
git worktree add --detach ../fusca-azul-legado v1.0.0
```
