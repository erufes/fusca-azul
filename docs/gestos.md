# Aplicativo de gestos

## Inicialização

Execute `uv run gestos` na raiz do projeto. A janela abre e inicia a câmera
padrão automaticamente. A captura, a preparação do modelo e o reconhecimento
rodam fora da thread da interface para manter a janela responsiva.

O vídeo é espelhado. O botão **Pausar câmera** libera a webcam; **Ativar câmera**
inicia uma nova sessão em modo Gestos. Para escolher outra câmera, pause,
altere o número e ative novamente. O controle **Pontos da mão** mostra ou oculta
a sobreposição dos 21 pontos, sem interromper o reconhecimento.

Falhas de permissão, abertura ou desconexão aparecem na janela. Corrija a causa
e use **Tentar novamente**. Ao fechar, o aplicativo solicita o encerramento e
aguarda a liberação da câmera e do detector. Se houver um download em andamento,
pode ser necessário aguardar a operação de rede terminar ou atingir seu timeout.

O aplicativo não abre portas de rede nem transmite imagens. A única conexão
externa feita pelo aplicativo é o download inicial do modelo, quando necessário.

## Gestos e modos

Use uma mão com a palma voltada para a câmera:

| Gesto | Resultado |
| --- | --- |
| Mão aberta (cinco dedos) | Em frente |
| Apenas mindinho levantado | Direita |
| Apenas polegar levantado | Esquerda |
| Indicador e médio levantados (V), demais fechados | Para trás |
| Punho fechado | Parado |
| Indicador e mindinho levantados (rock), demais fechados | Troca de modo |
| Outra combinação | Aguardando |
| Sem mão na imagem | Nenhuma mão |

Mantenha o rock por 1 segundo para alternar entre **Gestos** e **Automático**.
Desfaça o gesto por pelo menos meio segundo antes de trocar novamente. Manter
o rock não provoca trocas repetidas. Uma interrupção na captura reinicia a
contagem do gesto; pausar e reabrir a câmera começa uma sessão em modo Gestos.

Os gestos e a seleção de modo ainda não acionam motores nem executam navegação
autônoma: a integração com o firmware está pendente.

## Modelo

O aplicativo usa, nesta ordem:

1. O arquivo indicado pela variável de ambiente `FUSCA_MODEL`, se definida.
2. `src/gestos/model/hand_landmarker.task`, caso exista.
3. Um arquivo no cache do usuário, baixado automaticamente na primeira execução.

O cache fica em `fusca-azul/hand_landmarker.task` dentro de:

- Linux: `$XDG_CACHE_HOME` ou `~/.cache`.
- Windows: `%LOCALAPPDATA%`.
- macOS: `~/Library/Caches`.

Para preparar uma máquina sem internet, copie o
[modelo oficial](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task)
para o caminho local acima ou configure `FUSCA_MODEL`. As dependências Python
também precisam estar instaladas previamente. Um download interrompido não é
salvo como modelo completo. Se o modelo local estiver corrompido, remova esse
arquivo para permitir novo download ou substitua-o por uma cópia válida.

## Logs

Por padrão, os logs mostram início e encerramento da captura, trocas de modo
e erros. Para registrar apenas as mudanças de gesto, além dessas mensagens,
configure `FUSCA_LOG_LEVEL=debug` no ambiente antes de executar o aplicativo.
Por exemplo, no Linux/macOS:

```bash
FUSCA_LOG_LEVEL=debug uv run gestos
```

No PowerShell:

```powershell
$env:FUSCA_LOG_LEVEL = "debug"
uv run gestos
```

Não há logs por imagem. Avisos internos do MediaPipe podem aparecer no terminal.
