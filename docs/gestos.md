# Servidor de gestos

Para instalar e iniciar, siga o [README](../README.md#servidor-de-gestos).

## Página e reconhecimento

A página usa a câmera do navegador e envia imagens ao servidor. O botão
**Pausar câmera** interrompe a captura; o toggle **Pontos da mão** mostra ou
oculta os 21 pontos e suas conexões. A visualização é espelhada.

O reconhecimento considera uma mão, com a palma voltada para a câmera:

| Gesto | Resultado |
| --- | --- |
| Mão aberta (cinco dedos) | Em frente |
| Apenas mindinho levantado | Direita |
| Apenas polegar levantado | Esquerda |
| Indicador e médio levantados (V), demais fechados | Para trás |
| Punho fechado | Parado |
| Indicador e mindinho levantados (rock), demais fechados | Troca de modo |
| Outra combinação | Aguardando |
| Sem mão na imagem | Nenhuma mão detectada |

Para trocar entre **Gestos** e **Automático**, mantenha o rock por 1 segundo.
Ele alterna uma vez; desfaça o gesto por pelo menos meio segundo antes de
repetir. Uma pausa na captura interrompe a contagem. O modo pertence à conexão
do navegador e volta a Gestos ao reconectar. A página mostra o modo selecionado.

Os gestos e a seleção de modo ainda não acionam motores nem executam navegação
autônoma: a integração com o firmware está pendente.

O reconhecimento fica em `src/gestos/recognition.py`, o controle de modo em
`src/gestos/modes.py` e os textos dos gestos em `src/gestos/static/gestures.js`.

## Acesso pela rede

Ao executar `uv run gestos`, o terminal mostra a URL e um QR code para um
celular na mesma rede, usando a porta 8080. Sem endereço de rede disponível,
o link é local.

Para escolher outro endereço, por exemplo ao usar VPN ou HTTPS:

```bash
FUSCA_URL=https://seu-endereco/ uv run gestos
```

Essa opção muda apenas a URL anunciada e o QR code; não configura HTTPS.
O navegador exige HTTPS para liberar a câmera ao acessar pelo IP da rede,
tanto no celular quanto no computador. `http://localhost:8080/` é uma exceção
no próprio computador do servidor. A página mostra o aviso apenas ao clicar em
**Ativar câmera** por uma conexão insegura.

## Logs

Por padrão, são registrados conexões, desconexões e avisos, sem imprimir cada
imagem ou acesso à página. Erros continuam visíveis. Para acompanhar mudanças
de gesto:

```bash
FUSCA_LOG_LEVEL=debug uv run gestos
```

Mesmo nesse modo, gestos idênticos consecutivos não geram novas mensagens.
Avisos internos do MediaPipe podem aparecer na inicialização.
