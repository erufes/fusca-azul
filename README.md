# Fusca Azul

Esta é a nova versão do robô Fusca Azul, da ERUS/UFES. O software está sendo
reescrito e o hardware está em atualização. A documentação acompanha as
funcionalidades conforme são implementadas.

## Adições desta versão

- Servidor de reconhecimento de gestos com FastAPI e MediaPipe.
- Câmera pelo navegador, com página em modo escuro e controle para ativar ou pausar a captura.
- Desenho opcional dos 21 pontos da mão e suas conexões.
- Exibição dos gestos: em frente, parar e aguardando.
- QR code no terminal para abrir a página pela rede.
- Logs sem mensagens por imagem, com depuração de mudanças de gesto opcional.
- Firmware com PlatformIO para NodeMCU/ESP8266 e leitura de distância pelo VL53L0X, exibida no monitor serial.

O reconhecimento ainda não envia comandos ao robô. O controle dos motores e
a navegação autônoma da versão antiga ainda não foram integrados à nova versão.

## Organização

- [src/gestos/](src/gestos/): servidor e página web.
- [src/firmware/](src/firmware/): firmware atual.
- [docs/gestos.md](docs/gestos.md): uso do servidor, câmera e logs.
- [tests/](tests/): testes do servidor.

## Servidor de gestos

Requer Python 3.14 ou superior e uv. Na raiz do projeto:

```bash
uv sync
mkdir -p src/gestos/model
```

Se ainda não tiver o modelo, baixe-o uma vez:

```bash
curl --fail --location \
  https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task \
  --output src/gestos/model/hand_landmarker.task
```

Depois, inicie o servidor:

```bash
uv run gestos
```

Abra http://localhost:8080/ e ative a câmera. O terminal também mostra um QR code
com o endereço de acesso pela rede. Ao acessar pelo IP da rede, o navegador exige HTTPS para
liberar a câmera. A página avisa ao tentar ativá-la por uma conexão insegura.

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
