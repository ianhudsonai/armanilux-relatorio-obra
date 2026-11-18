---
name: relatorio-cronologico-obra
description: Gera o Relatório Cronológico de Obra da Armanilux (etapas A a L, sem etapa K) a partir do zip do WhatsApp, com transcrição local, dias úteis de São Paulo e arquivo Word. Use quando o usuário pedir o relatório da obra, o relatório cronológico, $relatorio-cronologico-obra, organizar o export do WhatsApp, transcrever áudios ou vídeos da obra, ou calcular dias úteis da instalação.
license: MIT
metadata:
  author: Armanilux
  version: "1.0"
  idioma: pt-BR
---

# Relatório Cronológico de Obra

Gere um Relatório Cronológico de Obra da Armanilux, em português do Brasil, formal, sem emoji. O entregável é um `.docx` na pasta `05-relatorios`. Não existe etapa K. Não envie áudio, vídeo, foto ou conversa para API de nuvem. Transcrição, feriados e o Word saem dos scripts desta pasta, neste computador.

Leia, antes de redigir ou corrigir o texto:

- `references/prompt-padrao.md` — etapas e o que cada uma exige
- `references/formato-relatorio.md` — cara do documento
- `references/dias-uteis.md` — regra de contagem
- `references/analise-json.md` — o que pode ser editado

O script já aplica esse formato. Não improvise outro sumário, não some intervalos como "atraso da Armanilux" e não invente data, nome ou prazo. O que não estiver no histórico fica escrito `dado não identificado`.

## Onde está o Python

Prefira o interpretador criado pelo `instalar.bat`:

`%USERPROFILE%\.armanilux-relatorio\venv\Scripts\python.exe`

No Linux ou no teste, use `python3`. Os comandos abaixo usam `PYTHON` para esse executável e `SKILL` para a pasta desta skill (a pasta que contém este arquivo).

Se faltar biblioteca, peça para a pessoa dar dois cliques em `instalar.bat` na pasta do repositório. Não rode `pip install` solto sem avisar. Se o Windows abrir a janela de permissão (UAC), quem clica em Sim é a pessoa; o Codex não consegue.

## 1. Preparar a pasta

Na primeira execução o script cria, se ainda não existir:

`%USERPROFILE%\Documents\Armanilux\Relatorios-de-Obra\<numero> - <cliente>\`

com `01-conversas`, `02-projetos-pdf`, `03-midias`, `04-transcricoes` e `05-relatorios`.

Se a pessoa informar o número da obra e o cliente, passe `--obra` e `--cliente`. Se não informar, o script tenta ler do próprio grupo. Não chute um nome de cliente.

## 2. Achar o zip

Procure, nesta ordem: o arquivo que a pessoa indicar, a pasta da obra, a pasta Downloads. Vale zip do WhatsApp ou um `.txt` de conversa já exportado. O zip original não é apagado.

Se não houver exportação, pare e explique, em português simples, como exportar no celular: abrir o grupo, tocar no nome, Exportar conversa, incluir mídia. Se o arquivo passar de uns 500 MB, oriente a exportar sem mídia e, se quiser, copiar só as fotos importantes para `03-midias`. O script ainda assim lê um zip grande em partes, sem carregar o arquivo inteiro na memória.

## 3. Rodar o pipeline

```bash
PYTHON SKILL/scripts/run_pipeline.py --obra "1001" --cliente "Nome do cliente" --zip "CAMINHO-DO-ZIP"
```

Omita `--obra`, `--cliente` ou `--zip` quando não souber; o script procura e lê o grupo. A primeira transcrição pode baixar o modelo Whisper `small` (uma vez, para o cache local). Se a pessoa não quiser esperar, rode com `--skip-transcribe` e deixe a fala como dado não identificado, dizendo isso com clareza.

Saídas:

- `04-transcricoes/analise.json` — fatos, dias úteis e textos
- `05-relatorios/figuras/dias-uteis.png` e `gantt.png`
- `05-relatorios/Relatorio-Cronologico-Obra-<numero>-vN.docx`

O PDF só aparece se o LibreOffice estiver instalado. O arquivo que vale é o Word.

## 4. Revisar a análise

Abra `analise.json` e confira cada evento contra o `.txt` da conversa. A classificação automática erra quando a frase é ambígua. Corrija `etapa`, `ocorrencia` e `impacto`. Não crie etapa K.

Abra as fotos e os quadros em `03-midias` (até três quadros por vídeo, não um filme inteiro). Para cada imagem que esclareça a obra, acrescente em `observacoes_visuais`:

```json
{"arquivo": "nome-do-arquivo.jpg", "observacao": "uma frase objetiva do que a imagem mostra"}
```

Se a imagem não mostrar nada útil, não invente. A observação continua `dado não identificado`.

Textos que você reescrever vão nestes campos, para o script não apagar na remontagem:

- `comentarios.<etapa>.ponto_critico` (e `gargalo`, `avaliacao`, `conclusao`, `intervalos_relevantes`, `situacao`)
- `recomendacoes_personalizadas` — lista de frases, sem o número na frente
- `conclusao_personalizada` — um texto só

Postura do texto: formal, neutra, a favor do registro da Armanilux, sem acusar pessoa. Intervalo em dias úteis não é atraso atribuído. Reprocesso, espera e dependência de obra (marcenaria, contrapiso, ponto hidráulico, medição pendente) precisam aparecer separados.

## 5. Remontar o Word

Depois de editar o JSON:

```bash
PYTHON SKILL/scripts/run_pipeline.py --rebuild-only --recalcular --obra-dir "PASTA-DA-OBRA"
```

`--recalcular` refaz dias úteis, indicadores e os parágrafos gerados a partir dos eventos corrigidos. Comentários, recomendações personalizadas, conclusão personalizada e observações visuais são mantidos.

Não entregue um Word escrito à mão por fora do script. O arquivo versionado (`v1`, `v2`, …) é o que a pessoa abre.

## 6. O que dizer à pessoa

Responda em português, curto, sem emoji. Informe o caminho completo do `.docx`, o número da versão, quantas pendências ficaram com status Pendente e se a transcrição rodou. Avise que o prazo contratual, quando for `dado não identificado`, não foi declarado no grupo, então o relatório não fala em atraso contratual.

Não copie a pasta da obra para o repositório público desta skill. Não publique o relatório em link aberto.

## Limites

- Feriados e dias úteis só pelo `scripts/business_days.py`. Não recalcule de cabeça e não use feriado de outro município.
- Áudio `.opus` e vídeo `.mp4` passam pelo Whisper local. Sem a biblioteca ou sem FFmpeg, registre a limitação; não mande o arquivo para um serviço externo.
- Nome de arquivo com caractere trocado (`Ãƒ`, `├`) é reparado na organização. Confira se o anexo citou o nome certo.
- Zip com caminho `..` é ignorado de propósito.
