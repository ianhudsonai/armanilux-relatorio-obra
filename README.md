# Relatório Cronológico de Obra — Armanilux

Quem for instalar no Codex cola esta linha, neste computador (não na nuvem):

```
https://github.com/ianhudsonai/armanilux-relatorio-obra instale as skills
```

O agente lê o `AGENTS.md` e instala as duas skills. Abra um chat novo e escreva `$preparar-projeto-armanilux`. Ele faz algumas perguntas e instala o que falta. Se pedir permissão, aprove. Se o Windows mostrar **Sim** ou **Não**, clique em **Sim**.

Depois, para cada obra, escreva `$relatorio-cronologico-obra` ou `faz o relatório da obra`.

Esta pasta ensina o computador a ler o grupo de WhatsApp de uma obra e entregar um **Relatório Cronológico de Obra** em Word. O relatório segue as etapas A, B, C, D, E, F, G, H, I, J e L (não existe etapa K), com dias úteis de São Paulo e as fotos, áudios e vídeos citados pelo nome.

Tudo roda **neste computador**. A conversa não vai para um serviço de transcrição na internet.

O exemplo que vem junto é inventado (Obra 1001, Família Almeida). Não é cliente real.

## Instalar

1. Abra o aplicativo **ChatGPT** no Windows (o aplicativo novo, não o site). Entre na sua conta. Escolha **Codex** e **Este computador**.
2. Cole a linha do começo desta página. Quando pedir para usar a internet ou rodar um comando, aprove.
3. Abra um chat novo e escreva `$preparar-projeto-armanilux`. Responda as perguntas. A pasta padrão é `Documentos\Armanilux`.

Não precisa procurar um arquivo para clicar. A instalação fica só no Codex, o aplicativo que você está usando. Não vai para outros programas.

Quem já tiver esta pasta no computador pode, se quiser, dar dois cliques em `instalar.bat`. Isso só instala as ferramentas. As perguntas ficam no Codex.

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

- A instalação parou com erro: leia a última frase na conversa do Codex. Sem internet, ela não termina. Peça o relatório de novo quando a rede voltar. Repetir não estraga o que já foi instalado.
- "Não encontrei o winget": instale o "Instalador de Aplicativo" pela Microsoft Store e peça o relatório outra vez.
- A skill não aparece no Codex: feche e abra o Codex. Confira se está em **Este computador**, não em Cloud.
- O Codex pede aprovação para usar a rede ou para rodar um comando: aprove. O relatório do dia a dia não precisa de rede, salvo a primeira vez do modelo de voz.
- Não saiu transcrição: o Word continua válido. A fala fica marcada como `dado não identificado`.
- Não saiu PDF: normal. Use o Word.
- O nome de um arquivo apareceu com letras trocadas (`Ã`, `├`): o script tenta corrigir. Se um anexo importante não entrou, diga o nome do arquivo na conversa do Codex.

## Privacidade

A obra tem nome de cliente e conversa interna. O Word fica na pasta do computador. Não publique esse arquivo num link aberto. Este repositório no GitHub é **público**: nunca coloque aqui zip, conversa ou relatório de obra real. O exemplo da pasta `examples` é fictício.

## Para o Ian (English)

This is an [Agent Skills](https://agentskills.io/specification) package aimed at Codex Local in the ChatGPT Windows app (Plus). Rogério installs it with `$skill-installer` from:

`https://github.com/ianhudsonai/armanilux-relatorio-obra/tree/main/skills/relatorio-cronologico-obra`

There are two skills. `preparar-projeto-armanilux` is once per person: questions, per-user winget, venv, ffmpeg, optional Whisper download, and `%USERPROFILE%\.armanilux-relatorio\config.json`. `relatorio-cronologico-obra` only writes the report and reads that config. Each skill folder is self-contained; the small `config_io.py` is duplicated so a copied skill does not need the other folder's code. The report skill may call the setup skill's `instalar.ps1` if both are installed and a library is missing.

The one-line paste is `https://github.com/ianhudsonai/armanilux-relatorio-obra instale as skills`. `AGENTS.md` tells the agent that `$skill-installer`'s `install-skill-from-github.py` rejects a bare repo URL (`Missing --path for GitHub URL`) and that the reliable call is one `--path` with both `skills/preparar-projeto-armanilux` and `skills/relatorio-cronologico-obra`. Install only into the app that is running these instructions, or only into the app the person named. Codex goes to `%USERPROFILE%\.codex\skills` (`~/.codex/skills`). Claude Code, when that is the agent running, goes to `~/.claude/skills`. Do not copy into the other app, and do not choose a destination by detecting that another tool is installed.

`skills/relatorio-cronologico-obra/scripts/run_pipeline.py` creates `Documents\Armanilux\Relatorios-de-Obra\<obra - cliente>\{01-conversas,02-projetos-pdf,03-midias,04-transcricoes,05-relatorios}`, streams the zip (zip-slip is dropped; mojibake filenames are repaired), parses Android and iPhone WhatsApp exports, transcribes speech locally, pulls a few video frames, reads PDF/docx, and writes a versioned docx. Business days are `(start, end]` excluding weekends, Brazilian national holidays, Carnival Monday and Tuesday, SP state 9 July, and São Paulo city 25 January and Corpus Christi (`holidays` subdiv São Paulo Capital, plus Carnival added in code). Ash Wednesday stays a business day. Intervals are not summed into an "Armanilux delay".

Codex is expected to review `04-transcricoes/analise.json`, look at photos/keyframes, and rerun with `--rebuild-only --recalcular`. Tests: `python -m unittest discover -s tests -v` (transcription is skipped in the sample run; CI does not install faster-whisper). Limitations: stage labels are keyword heuristics until Codex corrects them; visual descriptions stay `dado não identificado` until something that can see the image fills `observacoes_visuais`; PDF needs LibreOffice; the first Whisper `small` run downloads the model once.
