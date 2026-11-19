# Relatório Cronológico de Obra — Armanilux

Esta pasta ensina o computador a ler o grupo de WhatsApp de uma obra e entregar um **Relatório Cronológico de Obra** em Word. O relatório segue as etapas A, B, C, D, E, F, G, H, I, J e L (não existe etapa K), com dias úteis de São Paulo e as fotos, áudios e vídeos citados pelo nome.

Tudo roda **neste computador**. A conversa não vai para um serviço de transcrição na internet.

O exemplo que vem junto é inventado (Obra 1001, Família Almeida). Não é cliente real.

## Instalar

1. Abra o aplicativo **ChatGPT** no Windows (o aplicativo novo, não o site e não o "ChatGPT Classic"). Entre na sua conta. No menu, escolha **Codex**. Quando perguntar onde trabalhar, escolha **Este computador** (This computer), não Cloud.
2. Cole o link abaixo e, na linha seguinte, a frase. Quando o aplicativo pedir para usar a internet, aprove.

```
https://github.com/ianhudsonai/armanilux-relatorio-obra/tree/main/skills/relatorio-cronologico-obra
Instale esta skill com o skill-installer
```

Não precisa baixar o repositório nem procurar um arquivo para clicar. Na primeira vez que você pedir um relatório, o Codex instala o que falta neste computador. Se ele pedir permissão para rodar um comando, aprove. Se o Windows abrir uma janela **Sim** ou **Não**, clique em **Sim**.

Se a skill não aparecer, feche o Codex e abra de novo. Para instalar a skill outra vez, apague antes a pasta `%USERPROFILE%\.codex\skills\relatorio-cronologico-obra`.

Quem tiver a pasta inteira do repositório no computador pode, se quiser, dar dois cliques em `instalar.bat`. Isso é opcional. O caminho normal é só o link no Codex.

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

`$skill-installer` copies only `skills/relatorio-cronologico-obra/` into `%USERPROFILE%\.codex\skills\`. The installer lives at `scripts/instalar.ps1` inside that folder (root `instalar.bat` is an optional wrapper). On every run, `SKILL.md` tells Codex to check the venv and ffmpeg and, if anything is missing, run `powershell -ExecutionPolicy Bypass -File <skill>\scripts\instalar.ps1` itself. The user only approves the command and clicks Sim on UAC. Installs prefer `winget --scope user` (`Python.Python.3.12`) and a venv at `%USERPROFILE%\.armanilux-relatorio\venv` (`faster-whisper`, `python-docx`, `matplotlib`, `holidays`, `pdfplumber`, `pypdf`, Pillow, numpy). Afterward Codex re-reads PATH from the registry and continues in the same session. The script also prints `PYTHON=` and `FFMPEG=` and, when it finds ffmpeg outside PATH, adds that directory to the user PATH.

`skills/relatorio-cronologico-obra/scripts/run_pipeline.py` creates `Documents\Armanilux\Relatorios-de-Obra\<obra - cliente>\{01-conversas,02-projetos-pdf,03-midias,04-transcricoes,05-relatorios}`, streams the zip (zip-slip is dropped; mojibake filenames are repaired), parses Android and iPhone WhatsApp exports, transcribes speech locally, pulls a few video frames, reads PDF/docx, and writes a versioned docx. Business days are `(start, end]` excluding weekends, Brazilian national holidays, Carnival Monday and Tuesday, SP state 9 July, and São Paulo city 25 January and Corpus Christi (`holidays` subdiv São Paulo Capital, plus Carnival added in code). Ash Wednesday stays a business day. Intervals are not summed into an "Armanilux delay".

Codex is expected to review `04-transcricoes/analise.json`, look at photos/keyframes, and rerun with `--rebuild-only --recalcular`. Tests: `python -m unittest discover -s tests -v` (transcription is skipped in the sample run; CI does not install faster-whisper). Limitations: stage labels are keyword heuristics until Codex corrects them; visual descriptions stay `dado não identificado` until something that can see the image fills `observacoes_visuais`; PDF needs LibreOffice; the first Whisper `small` run downloads the model once.
