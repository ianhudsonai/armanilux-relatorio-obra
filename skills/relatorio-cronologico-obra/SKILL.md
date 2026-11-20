---
name: relatorio-cronologico-obra
description: Gera o Relatório Cronológico de Obra da Armanilux (etapas A a L, sem etapa K) a partir do zip do WhatsApp, com transcrição local, dias úteis de São Paulo e arquivo Word. Use quando pedirem o relatório da obra, o relatório cronológico, $relatorio-cronologico-obra, organizar o export do WhatsApp ou calcular dias úteis. Se não houver config.json, mande rodar $preparar-projeto-armanilux primeiro.
license: MIT
metadata:
  author: Armanilux
  version: "1.14"
  idioma: pt-BR
---

# Relatório Cronológico de Obra

Gere um Relatório Cronológico de Obra da Armanilux, em português do Brasil, formal, sem emoji. O entregável é um `.docx` na pasta `05-relatorios`. Não existe etapa K. Não mande áudio, vídeo, foto ou conversa para outro serviço na internet (de transcrição, tradução ou armazenamento): transcrição, feriados e o Word saem dos scripts desta pasta, neste computador. O que você mesmo lê para revisar passa pelo aplicativo em que você roda; o preparo já avisou a pessoa.

Leia, antes de redigir ou corrigir o texto:

- `references/revisao.md` — como revisar: o que ler, cada regra dos fatos, prazos e textos
- `references/prompt-padrao.md` — etapas e o que cada uma exige
- `references/formato-relatorio.md` — cara do documento
- `references/dias-uteis.md` — regra de contagem
- `references/analise-json.md` — o que pode ser editado

O script já aplica esse formato. Não improvise outro sumário, não some intervalos como "atraso da Armanilux" e não invente data, nome ou prazo. O que não estiver no histórico fica escrito `dado não identificado`.

## Preferências e ferramentas

Esta skill só faz o relatório. A preparação do computador é a skill `$preparar-projeto-armanilux`.

Antes de listar as conversas, leia `%USERPROFILE%\.armanilux-relatorio\config.json`. Se o arquivo não existir, pare e diga, em português, para abrir um chat e rodar `$preparar-projeto-armanilux`. Não invente pasta, nome nem função.

Se o arquivo existir, use `pasta_raiz`, `modelo_pasta_obra`, `nome`, `funcao` e `formato_entrega` (`word`, `pdf` ou `link`; config antigo usa `gerar_pdf`). O Python do relatório é `%USERPROFILE%\.armanilux-relatorio\venv\Scripts\python.exe`.

Confira também se esse Python importa docx, faster_whisper, matplotlib, holidays, PIL e numpy, e se o FFmpeg está no PATH (releia o PATH do registro antes). Se faltar biblioteca ou FFmpeg, ofereça rodar o instalador da outra skill, sem pedir para a pessoa procurar arquivo:

```powershell
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User') + ';' + "$env:LOCALAPPDATA\Microsoft\WinGet\Links"
powershell -ExecutionPolicy Bypass -File "<pasta-de-skills>\preparar-projeto-armanilux\scripts\instalar.ps1"
```

`<pasta-de-skills>` é a pasta que contém esta skill (a pasta acima de `relatorio-cronologico-obra`): a skill de preparo fica ao lado dela. Troque pelo caminho completo antes de rodar. Diga só isto: vai instalar o que falta; aprove o comando; se o Windows mostrar Sim ou Não, clique em Sim. É um comando longo (veja "Comandos longos"). Quando terminar, releia o PATH e continue o relatório. Se a outra skill não estiver instalada, mande rodar `$preparar-projeto-armanilux` num chat novo.

No Linux ou no teste, use `python3`. Nos comandos abaixo, `PYTHON` é o Python do ambiente e `SKILL` é a pasta desta skill.

## Comandos longos

O instalador e a primeira execução do pipeline (transcrição) podem passar de meia hora. Dê ao comando o tempo limite mais longo que o seu aplicativo permitir (60 minutos ou mais) ou rode em segundo plano; senão o aplicativo pode cortar o comando no meio. Se o comando parar no meio (inclusive por tempo limite), rode de novo: os dois continuam de onde pararam.

A pessoa não sabe que precisa pedir para você continuar. Fique no mesmo turno até o comando acabar e mostrar o código de saída: em segundo plano, acompanhe a saída até o fim, e siga o passo seguinte no mesmo turno. Se a sua resposta tiver de terminar antes, a última linha dela é: `O relatório ainda não terminou. Escreva "continue" para eu terminar.`

## 1. Preparar a pasta

A pasta dos relatórios é `Relatorios-de-Obra` dentro de `pasta_raiz` do config.json. Cada obra usa `modelo_pasta_obra` (padrão `{numero} - {cliente}`). Dentro da obra ficam `01-conversas`, `02-projetos-pdf`, `03-midias`, `04-transcricoes` e `05-relatorios`.

## 2. Achar as conversas

Nunca peça o caminho do zip. Rode primeiro, em toda execução:

```bash
PYTHON SKILL/scripts/run_pipeline.py --listar
```

O script procura em Downloads, Área de Trabalho (inclusive a do OneDrive) e na pasta da Armanilux, em subpastas também, e confere o conteúdo: zip com conversa do WhatsApp, ou `.txt` solto. Conversa repetida é ignorada. Mostre à pessoa, como está, a lista numerada que o script imprimir, e pergunte por qual começar. Ela pode escolher uma, várias ou todas.

Número da obra e cliente são adivinhados pelo nome do arquivo e pelo grupo, e podem vir errados (o número do apartamento no lugar do da obra, uma frase no lugar do cliente). Eles vão para o nome da pasta e para a capa do relatório. Antes de gerar, para cada conversa escolhida, faça uma pergunta de sim ou não com o que a lista mostrou, por exemplo: "Obra 8977, cliente Família Souza, certo?". A linha `arquivo:` da lista ajuda a pessoa a conferir.

- Sim: rode com `--indice`.
- Não: pergunte o número da obra e o nome do cliente certos e rode essa conversa sozinha, com os dois: `--indice 1 --obra "8977" --cliente "Família Souza"`. Com várias escolhidas, rode juntas só as confirmadas (`--indice 2,3`) e cada corrigida à parte; não use `--todas` quando alguma foi corrigida.
- O script disse que não conseguiu descobrir: pergunte só isso e rode do mesmo jeito.

```bash
PYTHON SKILL/scripts/run_pipeline.py --indice 1,3
PYTHON SKILL/scripts/run_pipeline.py --todas
```

Conversa nova de uma obra que já tem relatório aparece na lista como "próxima versão". Se a pessoa escolher, o relatório sai como v2 (primeiro como rascunho) na mesma pasta. Nunca gere sozinho.

O zip fica onde está até a pessoa dizer que o relatório está bom. Só então rode `PYTHON SKILL/scripts/run_pipeline.py --concluir --indice 1`: marca como concluída e move o zip para `01-conversas` da obra (`--copiar` deixa o original). O número vem da lista de relatórios prontos. O registro fica em `%USERPROFILE%\.armanilux-relatorio\registro.json`.

Se a lista vier vazia, explique como exportar no celular: grupo, nome do grupo, Exportar conversa. Se passar de uns 500 MB, pode exportar sem mídia.

## 3. Rodar o pipeline

Os comandos do passo 2 já rodam o pipeline. Com `--zip CAMINHO` (e `--obra`, `--cliente`) ele roda direto num arquivo que a pessoa indicou.

O script segue a resposta do preparo sobre os áudios (`baixar_modelo_whisper` no config.json). Com sim, a primeira vez pode baixar cerca de 484 MB, que ficam só neste computador; se a pessoa não quiser esperar, rode com `--skip-transcribe`. Com não, o script não transcreve nem baixa nada e avisa; se a pessoa mudar de ideia, rode de novo com `--transcrever`. Sem transcrição, diga que o que foi falado ficou como dado não identificado.

A transcrição é um comando longo (veja "Comandos longos"). O pipeline mostra "Transcrevendo N/total: arquivo"; cada áudio ou vídeo é transcrito uma vez só. Em segundo plano, enquanto isso, comece a ler a conversa (passo 4). Com `--skip-transcribe`, o que já foi transcrito continua no relatório.

Saídas:

- `04-transcricoes/analise.json` — fatos, dias úteis e textos
- `05-relatorios/figuras/dias-uteis.png` e `gantt.png`
- `05-relatorios/Relatorio-Cronologico-Obra-<numero>-vN-rascunho.docx` enquanto `revisado` não for `true`; com `"revisado": true` sai `...-vN.docx`, a versão que vale, com o mesmo número. A versão seguinte só começa com uma conversa nova da obra, e volta a ser rascunho.

Com entrega em PDF ou link, o script faz também o PDF, pelo Microsoft Word ou pelo LibreOffice deste computador; sem nenhum dos dois, sai só o Word e o script avisa. Com link, a versão revisada (nunca o rascunho) é copiada para a pasta do OneDrive ou do Google Drive gravada no preparo.

## 4. Revisar a análise

A leitura automática é só um rascunho, e esta revisão é obrigatória: não entregue o relatório sem ela. Leia `references/revisao.md` inteiro antes de abrir o `analise.json`; ele traz as regras de cada passo abaixo.

1. **Ler todo o material** (4.1): a conversa inteira, todas as transcrições, todos os textos de documento e todas as folhas de contato. Com subagentes, divida a conversa por período e as folhas entre eles.
2. **Registrar no `analise.json`** (4.2): fatos que faltaram, correções, programado e marco, frentes, etapa J, cores, conclusão, prazo contratual (só com fonte escrita da época), pendências, lacunas e os textos do relatório.
3. **Remontar** (4.3) com o comando do passo 5 até `04-transcricoes/verificacao.md` não listar nenhum fato e cada aviso da remontagem estar resolvido.
4. **Conferência independente** (4.4): um subagente novo, sem o contexto desta conversa, confere o conteúdo item por item; sem subagentes, uma segunda passada sua. Corrija tudo o que não for sustentado.
5. **Marcar como revisado** (4.5): só então grave `"revisado": true` e remonte. Com a conferência pendente, o script grava rascunho mesmo assim e diz por quê.

## 5. Remontar o Word

Depois de editar o JSON:

```bash
PYTHON SKILL/scripts/run_pipeline.py --rebuild-only --recalcular --obra-dir "PASTA-DA-OBRA"
```

`--recalcular` refaz dias úteis, marcos, cores sugeridas e o confronto com o prazo contratual a partir dos eventos corrigidos. Os textos escritos na revisão são mantidos.

Na última remontagem, a que vai para a pessoa, acrescente `--mostrar`: o script abre a pasta da obra com o Word já selecionado. Todo comando que grava o Word imprime uma linha `RELATORIO_WORD: <caminho>`; é por ela que você acha o arquivo. Quando sai PDF, vem também `RELATORIO_PDF: <caminho>`. Com entrega por link, a versão revisada imprime `RELATORIO_LINK: <caminho>`, a cópia na pasta da nuvem.

Entregue sempre o Word que o script gravou; o arquivo versionado (`v1`, `v2`, …) é o que a pessoa abre.

## 6. O que dizer à pessoa

A pessoa não precisa saber onde o arquivo fica. Entregue o Word na própria conversa: se o seu aplicativo tem uma ferramenta para enviar ou mostrar arquivo ao usuário, envie o `.docx` da linha `RELATORIO_WORD` (como anexo). Se não tem, rode a última remontagem com `--mostrar` para a pasta abrir com o arquivo selecionado. Nos dois casos, escreva também o caminho completo, numa linha só.

Siga a forma de entrega do preparo (`formato_entrega`). PDF: entregue o PDF da linha `RELATORIO_PDF` e diga que o Word está ao lado, para correções. Link: diga que o arquivo está na pasta do OneDrive ou do Google Drive (caminho da linha `RELATORIO_LINK`) e como mandar: clicar com o botão direito no arquivo, Compartilhar, e escolher só as pessoas que podem ver. O relatório tem dados do cliente: não sugira link aberto para qualquer pessoa. Se a linha de PDF ou de link não apareceu, entregue o Word e diga por quê, com a frase que o script imprimiu.

Responda em português, curto, sem emoji. Informe o número da versão, quantas pendências ficaram com status Pendente, se a transcrição rodou, quantos fatos a conferência confirmou e quantas lacunas o relatório registra. Diga se havia prazo contratual declarado no grupo ou nos documentos; sem ele, o relatório não fala em atraso contratual. Se ficou algum "Aviso de prazo", diga qual e por quê. Se o script avisou que a conversa parece cortada, diga a data em que ela começa e peça, se o grupo começou antes, uma exportação nova sem mídia.

Não copie a pasta da obra para o repositório público desta skill. Não publique o relatório em link aberto.

## Limites

- Feriados e dias úteis só pelo `scripts/business_days.py`. Não recalcule de cabeça e não use feriado de outro município.
- Áudio `.opus` e vídeo `.mp4` passam pelo Whisper local. Sem a biblioteca ou sem FFmpeg, registre a limitação; não mande o arquivo para um serviço externo.
- Nome de arquivo com caractere trocado (`Ãƒ`, `├`) é reparado na organização. Confira se o anexo citou o nome certo.
- Zip com caminho `..` é ignorado de propósito.
