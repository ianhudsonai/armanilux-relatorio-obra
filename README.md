# Relatório Cronológico de Obra — Armanilux

Esta pasta ensina o computador a ler o grupo de WhatsApp de uma obra e entregar um **Relatório Cronológico de Obra** em Word. O relatório segue as etapas A, B, C, D, E, F, G, H, I, J e L (não existe etapa K), com dias úteis de São Paulo e as fotos, áudios e vídeos citados pelo nome.

Tudo roda **neste computador**. A conversa não vai para um serviço de transcrição na internet.

O exemplo que vem junto é inventado (Obra 1001, Família Almeida). Não é cliente real.

## Instalar (uma vez)

1. Baixe esta pasta pelo botão verde **Code** e depois **Download ZIP** no GitHub. Extraia. Dê dois cliques em `instalar.bat` e espere a janela dizer que terminou. Se o Windows perguntar "Deseja permitir que este aplicativo faça alterações?", clique em **Sim**. Isso é a permissão de administrador (UAC). O instalador não aperta esse botão sozinho. Se a janela não aparecer, está tudo bem.
2. Abra o aplicativo **ChatGPT** no Windows (o aplicativo novo, não o site e não o "ChatGPT Classic"). Entre na sua conta. No menu, escolha **Codex**. Quando perguntar onde trabalhar, escolha **Este computador** (This computer), não Cloud.
3. Cole o link abaixo e, na linha seguinte, a frase. Quando o aplicativo pedir para usar a internet, aprove.

```
https://github.com/ianhudsonai/armanilux-relatorio-obra/tree/main/skills/relatorio-cronologico-obra
Instale esta skill com o skill-installer
```

Se a skill não aparecer, feche o Codex e abra de novo. Para instalar outra vez, apague antes a pasta `%USERPROFILE%\.codex\skills\relatorio-cronologico-obra`.

## Usar no dia a dia

1. No celular, abra o grupo da obra no WhatsApp. Toque no nome do grupo. Escolha **Exportar conversa** e **Incluir mídia** (com mídia).
2. Mande o zip para o computador e salve em **Downloads**, ou dentro da pasta da obra.
3. No Codex, neste computador, escreva por exemplo: `faz o relatório da obra 1001 do cliente Família Almeida`. Também pode chamar `$relatorio-cronologico-obra`.

O computador cria (se ainda não existir):

`Documentos\Armanilux\Relatorios-de-Obra\<número da obra - cliente>\`

Dentro dela:

| Pasta | O que fica |
| --- | --- |
| `01-conversas` | o texto do WhatsApp |
| `02-projetos-pdf` | PDF e Word de projeto |
| `03-midias` | fotos, áudios, vídeos e alguns quadros do vídeo |
| `04-transcricoes` | o que foi dito nos áudios, e a análise |
| `05-relatorios` | o Word, com versão no nome (`v1`, `v2`, …) |

Abra o arquivo `Relatorio-Cronologico-Obra-...-v1.docx` no Word. O PDF só é criado se o LibreOffice estiver instalado. O arquivo para mandar no grupo é o Word.

Na primeira obra com áudio, o computador baixa um modelo de transcrição (uma vez). Depois disso funciona sem internet.

## Se o zip for grande demais

Perto de 500 MB o e-mail e alguns programas recusam o arquivo. Nesse caso, no celular, exporte **sem mídia**. O texto e os PDF já bastam para o relatório. Se alguma foto for importante, copie só essa foto para a pasta `03-midias`.

O script ainda consegue abrir um zip grande, em partes, sem carregar tudo na memória. Só fica mais lento por causa dos vídeos.

O WhatsApp do Windows **não exporta** a conversa. A exportação é no celular.

## Se algo der errado

- A janela do `instalar.bat` fechou com erro: leia a última frase em vermelho. Sem internet, a instalação não termina. Rode de novo quando a rede voltar. Rodar de novo não estraga o que já foi instalado.
- "Não encontrei o winget": instale o "Instalador de Aplicativo" pela Microsoft Store e repita o passo 1.
- A skill não aparece no Codex: feche e abra o Codex. Confira se está em **Este computador**, não em Cloud.
- O Codex pede aprovação para usar a rede: aprove só na instalação. O relatório do dia a dia não precisa de rede, salvo a primeira vez do modelo de voz.
- Não saiu transcrição: o Word continua válido. A fala fica marcada como `dado não identificado`. Confira se o `instalar.bat` terminou e se o FFmpeg foi encontrado.
- Não saiu PDF: normal. Use o Word.
- O nome de um arquivo apareceu com letras trocadas (`Ã`, `├`): o script tenta corrigir. Se um anexo importante não entrou, diga o nome do arquivo na conversa do Codex.

## Privacidade

A obra tem nome de cliente e conversa interna. O Word fica na pasta do computador. Não publique esse arquivo num link aberto. Este repositório no GitHub é **público**: nunca coloque aqui zip, conversa ou relatório de obra real. O exemplo da pasta `examples` é fictício.

## Para o Ian (English)

This is an [Agent Skills](https://agentskills.io/specification) package aimed at Codex Local in the ChatGPT Windows app (Plus). Rogério installs it with `$skill-installer` from:

`https://github.com/ianhudsonai/armanilux-relatorio-obra/tree/main/skills/relatorio-cronologico-obra`

`instalar.bat` / `instalar.ps1` are idempotent: winget installs Python 3.12 and FFmpeg if missing (UAC is his click), then a venv at `%USERPROFILE%\.armanilux-relatorio\venv` gets `faster-whisper`, `python-docx`, `matplotlib`, `holidays`, `pdfplumber`, `pypdf`, Pillow and numpy.

`skills/relatorio-cronologico-obra/scripts/run_pipeline.py` creates `Documents\Armanilux\Relatorios-de-Obra\<obra - cliente>\{01-conversas,02-projetos-pdf,03-midias,04-transcricoes,05-relatorios}`, streams the zip (zip-slip is dropped; mojibake filenames are repaired), parses Android and iPhone WhatsApp exports, transcribes speech locally, pulls a few video frames, reads PDF/docx, and writes a versioned docx. Business days are `(start, end]` excluding weekends, Brazilian national holidays, Carnival Monday and Tuesday, SP state 9 July, and São Paulo city 25 January and Corpus Christi (`holidays` subdiv São Paulo Capital, plus Carnival added in code). Ash Wednesday stays a business day. Intervals are not summed into an "Armanilux delay".

Codex is expected to review `04-transcricoes/analise.json`, look at photos/keyframes, and rerun with `--rebuild-only --recalcular`. Tests: `python -m unittest discover -s tests -v` (transcription is skipped in the sample run; CI does not install faster-whisper). Limitations: stage labels are keyword heuristics until Codex corrects them; visual descriptions stay `dado não identificado` until something that can see the image fills `observacoes_visuais`; PDF needs LibreOffice; the first Whisper `small` run downloads the model once.
