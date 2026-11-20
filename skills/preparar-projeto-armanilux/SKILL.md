---
name: preparar-projeto-armanilux
description: Prepara o computador de alguém da Armanilux para os relatórios de obra. Use na primeira vez, ou quando pedirem $preparar-projeto-armanilux, instalar ferramentas, mudar a pasta da Armanilux, o nome do responsável, a função, a forma de entrega (Word, PDF ou link) ou o nome das pastas de obra. Faz as perguntas, instala Python, FFmpeg e as bibliotecas neste computador e grava config.json.
license: MIT
metadata:
  author: Armanilux
  version: "1.4"
  idioma: pt-BR
---

# Preparar o projeto Armanilux

Esta skill roda uma vez por pessoa, ou de novo quando ela quiser mudar as preferências. Fale sempre em português, sem emoji. Não peça para a pessoa procurar arquivo nem dar dois cliques em nada.

A pasta desta skill é a pasta deste arquivo. O instalador é `scripts/instalar.ps1`.

## 1. Perguntar

Se já existir `%USERPROFILE%\.armanilux-relatorio\config.json`, leia e use os valores como sugestão. Faça estas perguntas, uma de cada vez, em português simples:

1. Você já tem uma pasta da Armanilux neste computador? Se tiver, me diga onde ela está. Se não tiver, eu crio em Documentos, com o nome Armanilux.
2. Qual é o seu nome e qual é o seu cargo na Armanilux? Os dois aparecem no topo do relatório.
3. Quando o relatório ficar pronto, como você quer receber? Em Word, em PDF, ou por link (o arquivo vai para o seu OneDrive ou Google Drive e você manda o link para quem precisa).
4. Como quer o nome da pasta de cada obra? O mais comum é o número e depois o cliente, por exemplo "1001 - Família Almeida". Se preferir, o cliente pode vir primeiro, ou só o número.
5. Quer que eu também entenda os áudios e vídeos das conversas? Isso precisa de um download único (cerca de 484 MB), mas é seguro e fica só no seu computador. Sim ou não.

Na pergunta 3, o Word é sempre gravado também, porque é o arquivo que dá para corrigir. Link só funciona se o OneDrive ou o Google Drive estiver instalado e conectado neste computador.

Na pergunta 5, use esse texto. O arquivo baixado (modelo small, `model.bin`) tem 483.546.902 bytes, cerca de 484 MB. Não diga "modelo", "Whisper" nem "transcrição" para a pessoa.

Na pergunta 4, cada opção mostra um exemplo, porque só o nome da regra é difícil de entender. Use estas opções, com estes exemplos (e, se já houver configuração, diga qual é a atual com o exemplo dela):

- Número e depois cliente, por exemplo "1001 - Família Almeida"
- Cliente e depois número, por exemplo "Família Almeida - 1001"
- Só o número, por exemplo "1001"

Não invente resposta. Se a pessoa não souber onde fica a pasta, use Documentos\Armanilux. Na pergunta 4, grave `{numero} - {cliente}`, `{cliente} - {numero}` ou `{numero}`, conforme a escolha, sem mostrar esses códigos para ela.

## 2. Instalar as ferramentas

Diga uma frase: vai instalar o que falta neste computador; quando o aplicativo pedir permissão, aprove; se o Windows abrir Sim ou Não, clique em Sim.

Releia o PATH e execute o instalador desta pasta. Use `-BaixarModelo` só se a pessoa disse sim na pergunta 5. Use `-Pdf` se ela escolheu PDF ou link na pergunta 3: o instalador confere se há Microsoft Word ou LibreOffice e, sem nenhum dos dois, instala o LibreOffice (gratuito, cerca de 350 MB; o Windows pode pedir Sim).

```powershell
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User') + ';' + "$env:LOCALAPPDATA\Microsoft\WinGet\Links"
powershell -ExecutionPolicy Bypass -File "<pasta-desta-skill>\scripts\instalar.ps1"
```

O instalador aceita um Python 3.10 a 3.13 que já exista; fora disso, instala com `winget install Python.Python.3.12 --scope user`, e o mesmo escopo para o FFmpeg. O pip fica em `%USERPROFILE%\.armanilux-relatorio\venv`, com as versões fixas de `scripts/requirements.txt`; um ambiente antigo de outro Python é guardado ao lado como `venv-antigo-<data>` e refeito. Pode rodar de novo. Se já estiver instalado, só confere.

O instalador pode levar de 10 a 40 minutos (bibliotecas e, com sim na pergunta 5, o download de cerca de 484 MB). Dê ao comando o tempo limite mais longo que o seu aplicativo permitir (60 minutos ou mais) ou rode em segundo plano e espere terminar. Se o aplicativo cortar o comando por tempo, rode de novo: o que já foi instalado fica, e ele continua.

Se terminar com erro, explique em português e pare. Não mande a pessoa atrás de um arquivo.

Quando terminar com código 0, releia o PATH na mesma sessão. Use o `PYTHON=` que o instalador imprimiu. Não peça para reiniciar o computador.

## 3. Gravar preferências e pastas

Com o Python do ambiente:

```powershell
& "$env:USERPROFILE\.armanilux-relatorio\venv\Scripts\python.exe" "<pasta-desta-skill>\scripts\preparar.py" --pasta-raiz "CAMINHO" --nome "NOME" --funcao "FUNCAO" --entrega pdf --modelo "{numero} - {cliente}" --baixar-modelo nao
```

`--entrega` é `word`, `pdf` ou `link`. Com `link`, antes rode o mesmo `preparar.py` só com `--listar-nuvens`: cada linha `NUVEM:` é uma pasta do OneDrive ou do Google Drive deste computador, já com `Armanilux\Relatorios` no fim. Se vier mais de uma, pergunte em qual a pessoa quer ("OneDrive ou Google Drive?"). Passe a escolhida em `--pasta-link "CAMINHO"`. Com uma só, pode usar `--pasta-link auto`, o padrão. Se a pessoa disser outra pasta, passe essa. Se o script disser que não achou a pasta da nuvem, ele grava PDF: conte isso para a pessoa. `--baixar-modelo` é `sim` ou `nao`.

Isso grava `config.json`, cria a pasta escolhida, `Relatorios-de-Obra\_modelo` com as cinco subpastas, e um `LEIA-ME.txt` na pasta raiz. Rodar de novo só atualiza as preferências. Não apaga obras já existentes.

## 4. Encerrar

Diga onde ficou a pasta, o nome que vai no relatório e como o relatório vai ser entregue (Word, PDF ou link, com a pasta da nuvem). Diga que, para cada obra, o próximo chat usa `$relatorio-cronologico-obra`.

Diga também, curto e sem esconder: os áudios e os vídeos viram texto neste computador, mas para escrever o relatório o ChatGPT lê a conversa da obra, o texto dos áudios, os documentos e as fotos. Peça para, no ChatGPT, abrir Configurações, Controles de dados, e desligar "Melhorar o modelo para todos", para as conversas das obras não serem usadas no treino do modelo.
