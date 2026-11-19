---
name: relatorio-cronologico-obra
description: Gera o Relatório Cronológico de Obra da Armanilux (etapas A a L, sem etapa K) a partir do zip do WhatsApp, com transcrição local, dias úteis de São Paulo e arquivo Word. Use quando pedirem o relatório da obra, o relatório cronológico, $relatorio-cronologico-obra, organizar o export do WhatsApp ou calcular dias úteis. Se não houver config.json, mande rodar $preparar-projeto-armanilux primeiro.
license: MIT
metadata:
  author: Armanilux
  version: "1.2"
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

## Preferências e ferramentas

Esta skill só faz o relatório. A preparação do computador é a skill `$preparar-projeto-armanilux`.

Antes de listar as conversas, leia `%USERPROFILE%\.armanilux-relatorio\config.json`. Se o arquivo não existir, pare e diga, em português, para abrir um chat e rodar `$preparar-projeto-armanilux`. Não invente pasta, nome nem função.

Se o arquivo existir, use `pasta_raiz`, `modelo_pasta_obra`, `nome`, `funcao` e `gerar_pdf`. O Python do relatório é `%USERPROFILE%\.armanilux-relatorio\venv\Scripts\python.exe`.

Confira também se esse Python importa docx, faster_whisper, matplotlib, holidays, PIL e numpy, e se o FFmpeg está no PATH (releia o PATH do registro antes). Se faltar biblioteca ou FFmpeg, ofereça rodar o instalador da outra skill, sem pedir para a pessoa procurar arquivo:

```powershell
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User') + ';' + "$env:LOCALAPPDATA\Microsoft\WinGet\Links"
powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.codex\skills\preparar-projeto-armanilux\scripts\instalar.ps1"
```

Diga só isto: vai instalar o que falta; aprove o comando; se o Windows mostrar Sim ou Não, clique em Sim. Quando terminar, releia o PATH e continue o relatório. Se a outra skill não estiver instalada, mande rodar `$preparar-projeto-armanilux` num chat novo.

No Linux ou no teste, use `python3`. Nos comandos abaixo, `PYTHON` é o Python do ambiente e `SKILL` é a pasta desta skill.

## 1. Preparar a pasta

A pasta dos relatórios é `Relatorios-de-Obra` dentro de `pasta_raiz` do config.json. Cada obra usa `modelo_pasta_obra` (padrão `{numero} - {cliente}`).

Dentro da obra ficam `01-conversas`, `02-projetos-pdf`, `03-midias`, `04-transcricoes` e `05-relatorios`.

Se a pessoa informar o número da obra e o cliente, passe `--obra` e `--cliente`. Se não informar, o script tenta ler do próprio grupo. Não chute um nome de cliente.

## 2. Achar as conversas

Nunca peça o caminho do zip. Rode primeiro, em toda execução:

```bash
PYTHON SKILL/scripts/run_pipeline.py --listar
```

O script procura em Downloads, Área de Trabalho (inclusive a do OneDrive) e na pasta da Armanilux, em subpastas também. Reconhece nome longo, com acento e parênteses, e confere o conteúdo: zip com conversa do WhatsApp, ou `.txt` solto. Conversa igual com outro nome (ou baixada duas vezes) é ignorada. Mostre à pessoa, como está, a lista numerada que o script imprimir, e pergunte por qual começar. Ela pode escolher uma, várias ou todas.

Número da obra e cliente saem sozinhos do nome do arquivo e do grupo. Só pergunte se o script disser que não conseguiu, e então pergunte só isso e rode com `--obra` e `--cliente`.

Gerar o relatório (uma conversa de cada vez, em lote):

```bash
PYTHON SKILL/scripts/run_pipeline.py --indice 1,3
PYTHON SKILL/scripts/run_pipeline.py --todas
```

Conversa nova de uma obra que já tem relatório aparece na lista como "próxima versão". Se a pessoa escolher, o relatório sai como v2 na mesma pasta. Nunca gere sozinho.

O zip fica onde está até a pessoa dizer que o relatório está bom. Só então:

```bash
PYTHON SKILL/scripts/run_pipeline.py --concluir --indice 1
```

Isso marca como concluída e move o zip para `01-conversas` da obra (`--copiar` deixa o original). O número vem da lista de relatórios prontos. O registro fica em `%USERPROFILE%\.armanilux-relatorioegistro.json`.

Se a lista vier vazia, explique como exportar no celular: grupo, nome do grupo, Exportar conversa. Se passar de uns 500 MB, pode exportar sem mídia. O script lê um zip grande em partes e não envia nada para a internet.

## 3. Rodar o pipeline

```bash
PYTHON SKILL/scripts/run_pipeline.py --obra "1001" --cliente "Nome do cliente" --zip "CAMINHO-DO-ZIP"
```

Os comandos do passo 2 já rodam o pipeline. Com `--zip CAMINHO` o pipeline roda direto num arquivo que a pessoa indicou. Se a pessoa pediu para entender os áudios, a primeira vez pode baixar cerca de 484 MB e ficar só neste computador. Se ela não quiser esperar, rode com `--skip-transcribe` e diga que o que foi falado ficou como dado não identificado.

Saídas:

- `04-transcricoes/analise.json` — fatos, dias úteis e textos
- `05-relatorios/figuras/dias-uteis.png` e `gantt.png`
- `05-relatorios/Relatorio-Cronologico-Obra-<numero>-vN.docx`

O PDF só aparece se o LibreOffice estiver instalado. O arquivo que vale é o Word.

## 4. Revisar a análise

A leitura automática é só um rascunho: num grupo grande ela deixa etapas vazias (chapas, medição, entrega, conclusão) e pode classificar errado. Esta revisão é obrigatória, não opcional. Não entregue o relatório sem ela.

1. Abra `04-transcricoes/candidatos-por-etapa.md`. Ele lista, por etapa, as mensagens do grupo que provavelmente falam dela, em ordem de data. A lista é larga de propósito: confira cada mensagem e use só as que realmente marcam a etapa. Se precisar de mais contexto, procure a mensagem no `.txt` em `01-conversas`.
2. Para cada fato real que faltou, acrescente em `eventos_adicionais` do `analise.json`:

```json
{"data": "2026-01-13", "hora": "10:30", "etapa": "C", "autor": "Nome", "ocorrencia": "Medição in loco realizada na cozinha.", "impacto": ""}
```

`impacto` só vale na etapa J. Etapa é uma letra de A a J ou L. Se a mensagem trouxer arquivo, ponha o nome em `midias` ou `documentos`.
3. Para tirar um fato que a leitura automática classificou errado, use `ajustes_eventos` com `{"data": "2026-01-13", "hora": "10:30", "etapa_original": "J", "remover": true}`. Para só trocar a etapa, use `"etapa": "C"` no lugar de `remover`.
4. Confira também a lista de pendências (`pendencias`) e o endereço e demais campos de `obra`. Apague o que não for pendência de verdade.
5. Não invente data nem fato. O que o grupo não diz fica `dado não identificado`. Não crie etapa K.
6. O diagnóstico automático é genérico e não pode ficar como está num relatório revisado. Escreva, com fatos do grupo e datas, em `analise.json`:
   - `diagnostico_prompt`: `{"reprocessos": "...", "tempos_ociosos": "...", "atrasos_internos": "...", "dependencias_externas": "..."}`, os quatro blocos que o prompt padrão exige. O que o grupo não sustenta fica `dado não identificado`.
   - `gargalos_personalizados`: lista de `{"titulo": "...", "texto": "..."}`.
   - `responsabilidades_personalizadas`: lista de `{"natureza": "...", "diagnostico": "..."}`.
   - `produtividade_personalizada`: um texto sobre o impacto da etapa J na produtividade.
   - `obra_ajustes`: campos de `obra` que o grupo não traz em formato fixo (`construtora`, `engenheiro`, `arquitetura`, `responsavel_armanilux`, `endereco`, `prazo_contratual`).
   - `pendencias_revisadas`: lista `{"item": "...", "status": "Pendente"}` com só as pendências reais.
7. Só depois de revisar tudo isso, grave `"revisado": true` no `analise.json`. Sem isso o Word sai com a faixa vermelha "RASCUNHO NÃO REVISADO" no topo, de propósito, para ninguém enviar um relatório sem conferência.

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
