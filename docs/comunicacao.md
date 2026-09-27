# Wi-Fi e comunicação com o robô

## Preparar e conectar

1. Na pasta do projeto, execute `uv sync` e `uv run gestos` no computador.
2. Compile com `pio run` e grave o NodeMCU com `pio run --target upload`.
3. Sem configuração salva, o robô cria a rede aberta `Fusca-Azul-<identificador>`.
   Conecte um celular ou computador a essa rede. Se o portal não abrir
   automaticamente, acesse **http://192.168.4.1** (HTTP, sem HTTPS).
4. Informe o nome exato e a senha da rede **2,4 GHz**. Redes abertas aceitam
   senha vazia. Redes empresariais com usuário/certificado não são suportadas.
5. O robô tenta conectar por até 20 segundos. Só depois de conectar e obter IP
   ele grava a configuração e reinicia. Se falhar, o portal continua disponível
   e a rede anterior permanece salva. Atualize a página para ver o resultado.
   A mudança de canal ao testar a rede pode exigir reconectar ao hotspot.
6. Volte o computador à mesma rede do robô. Abra a aplicação nessa rede:
   ela deve mostrar **Robô conectado** quando começar a responder às consultas.

O robô inicia com os motores parados. No primeiro teste, mantenha as rodas
suspensas e verifique frente, ré, curvas e parada antes de colocá-lo no chão.

## Memória e reconexão

Apenas um par SSID/senha fica em `/wifi.bin`, no LittleFS. A nova configuração
é escrita em arquivo temporário e substitui a anterior por rename após uma
conexão bem-sucedida. Não há lista de redes ou gravações a cada comando.
As credenciais não são impressas no monitor serial nem devolvidas pelo portal.

A cada boot, o firmware lê essa configuração e verifica a conexão Wi-Fi.
Se não conectar em 20 segundos, abre o hotspot. Se perder uma conexão em uso,
para os motores, tenta novamente a rede salva e abre o hotspot se necessário.
Enquanto o portal estiver ocioso, volta a tentar a última rede a cada 30 segundos.
Uma rede ausente ou senha incorreta não apaga a última configuração válida.
Para trocar de rede, torne a anterior indisponível para o robô e use o portal.

O hotspot é aberto, destinado à configuração local por proximidade, e é fechado
quando a conexão normal se estabelece. SSID e senha ficam na flash sem criptografia.
O protocolo de comando também não possui autenticação ou criptografia: use uma
rede local confiável. A aplicação não envia vídeo para o robô.

## Descoberta e protocolo v1

A aplicação anuncia `_fusca-azul._tcp.local.` por mDNS/DNS-SD, com TXT `version=1`,
porta TCP **8765** e os endereços IPv4 locais disponíveis no momento da abertura.
O robô consulta esse serviço, obtém IP/porta e inicia a conexão TCP.
Não depende de internet, IP fixo ou um servidor DNS externo.

Mantenha uma única aplicação servidora na rede: se a consulta retornar mais de
um servidor, o robô permanece parado e repete a descoberta a cada cinco segundos.
Uma conexão já estabelecida continua com o servidor escolhido até ser perdida.
Se o computador trocar de rede/endereço, reabra a aplicação para atualizar o anúncio.

A cada 100 ms o robô envia uma linha ASCII:

```text
FUSCA/1 GET
```

A aplicação responde uma linha ASCII, terminada em `\n`:

```text
FUSCA/1 FRENTE
```

Comandos aceitos: `FRENTE`, `RE`, `ESQUERDA`, `DIREITA`, `PARAR`.
Há apenas uma consulta pendente por vez. Respostas incompletas, desconhecidas,
longas demais ou recebidas sem uma consulta encerram a conexão e param o robô.
Sem resposta em 400 ms, o firmware para e volta à descoberta. Entre respostas,
o próximo pedido ocorre no intervalo de 100 ms. Escritas TCP têm timeout de 100 ms.

O servidor converte reconhecimento sem atualização por mais de 400 ms em
`PARAR`. No controle manual, sem mão, gesto desconhecido ou rock também
produzem `PARAR`. No modo Automático, a fonte de comandos é a análise recente
da ESP32-CAM; veja [navegação visual](espcam.md). Pausar, trocar câmera, erro de captura e fechamento invalidam o comando.
A parada não é frenagem ativa: a ponte é desabilitada e as rodas desaceleram.

## Diagnóstico e validação

- Permita TCP 8765 e mDNS UDP 5353 no firewall do computador.
- Desative isolamento entre clientes no ponto de acesso. Redes de convidados
  podem impedir comunicação local ou multicast mesmo com Wi-Fi conectado.
- Veja as mensagens `[WIFI]` e `[SERVIDOR]` em `pio device monitor` a 115200 baud.
- Erros de inicialização do servidor aparecem na interface; corrija e reabra.
- Testes da aplicação: `uv run python -m unittest discover -s tests -v`.
- Compilação do firmware: `pio run`.

Valide na placa: primeira configuração, senha errada, desligar e religar,
substituir a rede, queda do roteador, servidor ausente, servidor reiniciado e
perda da câmera durante movimento. Testes Python não validam rádio, flash ou motores.

Referências das APIs usadas: [ESP8266 mDNS/DNS-SD](https://github.com/esp8266/Arduino/blob/master/libraries/ESP8266mDNS/examples/mDNS-SD_Extended/mDNS-SD_Extended.ino),
[LittleFS](https://arduino-esp8266.readthedocs.io/en/latest/filesystem.html) e
[python-zeroconf](https://python-zeroconf.readthedocs.io/en/latest/api.html).
