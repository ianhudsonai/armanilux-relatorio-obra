---
name: relatorio-cronologico-obra
description: Gera o Relatório Cronológico de Obra da Armanilux (etapas A a L, sem etapa K) a partir do zip do WhatsApp, com transcrição local, dias úteis de São Paulo e arquivo Word. Use quando pedirem o relatório da obra, o relatório cronológico, $relatorio-cronologico-obra, organizar o export do WhatsApp ou calcular dias úteis. Se não houver config.json, mande rodar $preparar-projeto-armanilux primeiro.
license: MIT
metadata:
  author: Armanilux
  version: "1.12"
  idioma: pt-BR
---

# Relatório Cronológico de Obra

Gere um Relatório Cronológico de Obra da Armanilux, em português do Brasil, formal, sem emoji. O entregável é um `.docx` na pasta `05-relatorios`. Não existe etapa K. Não mande áudio, vídeo, foto ou conversa para outro serviço na internet (de transcrição, tradução ou armazenamento): transcrição, feriados e o Word saem dos scripts desta pasta, neste computador. O que você mesmo lê para revisar passa pelo aplicativo em que você roda; o preparo já avisou a pessoa.

Leia, antes de redigir ou corrigir o texto:

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

`<pasta-de-skills>` é a pasta que contém esta skill (a pasta acima de `relatorio-cronologico-obra`): a skill de preparo fica ao lado dela. Troque pelo caminho completo antes de rodar. Diga só isto: vai instalar o que falta; aprove o comando; se o Windows mostrar Sim ou Não, clique em Sim. Quando terminar, releia o PATH e continue o relatório. Se a outra skill não estiver instalada, mande rodar `$preparar-projeto-armanilux` num chat novo.

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

Número da obra e cliente são adivinhados pelo nome do arquivo e pelo grupo, e podem vir errados (o número do apartamento no lugar do da obra, uma frase no lugar do cliente). Eles vão para o nome da pasta e para a capa do relatório. Antes de gerar, para cada conversa escolhida, faça uma pergunta de sim ou não com o que a lista mostrou, por exemplo: "Obra 8977, cliente Família Souza, certo?". A linha `arquivo:` da lista ajuda a pessoa a conferir.

- Sim: rode com `--indice`.
- Não: pergunte o número da obra e o nome do cliente certos e rode essa conversa sozinha, com os dois: `--indice 1 --obra "8977" --cliente "Família Souza"`. Com várias escolhidas, rode juntas só as confirmadas (`--indice 2,3`) e cada corrigida à parte; não use `--todas` quando alguma foi corrigida.
- O script disse que não conseguiu descobrir: pergunte só isso e rode do mesmo jeito.

Gerar o relatório (uma conversa de cada vez, em lote):

```bash
PYTHON SKILL/scripts/run_pipeline.py --indice 1,3
PYTHON SKILL/scripts/run_pipeline.py --todas
```

Conversa nova de uma obra que já tem relatório aparece na lista como "próxima versão". Se a pessoa escolher, o relatório sai como v2 (primeiro como rascunho) na mesma pasta. Nunca gere sozinho.

O zip fica onde está até a pessoa dizer que o relatório está bom. Só então:

```bash
PYTHON SKILL/scripts/run_pipeline.py --concluir --indice 1
```

Isso marca como concluída e move o zip para `01-conversas` da obra (`--copiar` deixa o original). O número vem da lista de relatórios prontos. O registro fica em `%USERPROFILE%\.armanilux-relatorio\registro.json`.

Se a lista vier vazia, explique como exportar no celular: grupo, nome do grupo, Exportar conversa. Se passar de uns 500 MB, pode exportar sem mídia. O script lê um zip grande em partes e não envia nada para a internet.

## 3. Rodar o pipeline

```bash
PYTHON SKILL/scripts/run_pipeline.py --obra "1001" --cliente "Nome do cliente" --zip "CAMINHO-DO-ZIP"
```

Os comandos do passo 2 já rodam o pipeline. Com `--zip CAMINHO` o pipeline roda direto num arquivo que a pessoa indicou. O script segue a resposta do preparo sobre os áudios (`baixar_modelo_whisper` no config.json). Com sim, a primeira vez pode baixar cerca de 484 MB, que ficam só neste computador; se a pessoa não quiser esperar, rode com `--skip-transcribe`. Com não, o script não transcreve nem baixa nada e avisa; se a pessoa mudar de ideia, rode de novo com `--transcrever`. Sem transcrição, diga que o que foi falado ficou como dado não identificado.

A transcrição demora: em obra com dezenas de áudios e vídeos passa de meia hora. Antes de rodar o pipeline, dê ao comando o tempo limite mais longo que o seu aplicativo permitir (60 minutos ou mais) ou rode em segundo plano; senão o aplicativo pode cortar o comando no meio. Em segundo plano, enquanto isso, comece a ler a conversa (passo 4). O pipeline mostra "Transcrevendo N/total: arquivo". Cada áudio ou vídeo é transcrito uma vez só: se o comando parar no meio (inclusive por tempo limite), rode de novo e ele continua de onde parou. Com `--skip-transcribe`, o que já foi transcrito continua no relatório.

Saídas:

- `04-transcricoes/analise.json` — fatos, dias úteis e textos
- `05-relatorios/figuras/dias-uteis.png` e `gantt.png`
- `05-relatorios/Relatorio-Cronologico-Obra-<numero>-vN-rascunho.docx` enquanto `revisado` não for `true`: cada remontagem regrava o mesmo rascunho. Com `"revisado": true` sai `...-vN.docx`, a versão que vale, com o mesmo número do rascunho; o rascunho vai para `05-relatorios/rascunhos/`. Remontar depois disso regrava o mesmo `vN` (corrigir um erro não gasta versão). A versão seguinte só começa com uma conversa nova da obra, e volta a ser rascunho.

Com entrega em PDF ou link, o script faz também o PDF, pelo Microsoft Word ou pelo LibreOffice deste computador. Se nenhum dos dois existir, sai só o Word e o script avisa. Com link, a versão revisada (nunca o rascunho) é copiada para a pasta do OneDrive ou do Google Drive gravada no preparo.

## 4. Revisar a análise

A leitura automática é só um rascunho: num grupo grande ela deixa etapas vazias (chapas, medição, entrega, conclusão) e pode classificar errado. Esta revisão é obrigatória, não opcional. Não entregue o relatório sem ela.

Leia todo o material para entender a obra por completo; escreva um relatório curto e correto. Tudo o que entra precisa estar no grupo: numa mensagem, numa transcrição, num documento ou numa imagem. O que você não conseguiu ler ou confirmar não some: vira lacuna, numa frase curta.

### 4.1 Ler todo o material

Leia tudo antes de escrever. Não basta a lista de candidatos.

- **Conversa inteira.** Leia o `.txt` de `01-conversas` do começo ao fim. Se o seu aplicativo permitir subagentes e a conversa for grande, divida por período (por exemplo, um subagente por trimestre) e peça a cada um: por data, os fatos de cada etapa com data, hora, autor e o trecho exato da mensagem; as pendências; quem é quem (empresa, função). Sem subagentes, leia você mesmo, em partes. `04-transcricoes/candidatos-por-etapa.md` serve de índice, não de limite.
- **Mensagens coladas.** No `.txt`, mensagem de outra conversa colada no grupo aparece como uma linha dentro da mensagem de quem colou, no formato `[12:25, 03/07/2026] Nome: texto` ou `[03/07, 12:25] Nome: texto`. A data, a hora e o autor do fato são os dessa linha (os originais); quem colou e quando é a mensagem em volta. No `analise.json`, o fato que veio de uma colada termina com "(encaminhada no grupo por … em …)".
- **Áudios e vídeos.** Leia todas as transcrições em `analise.json` (`transcricoes`), não só as que parecem relevantes. Vídeo muitas vezes é o registro de uma visita ou de uma medição e traz a data e o fato que faltam no texto.
- **Documentos.** Leia o texto de cada documento em `documentos_texto` (projetos, folhas de medição, cronogramas, memoriais). Documento sem texto (desenho técnico) aparece nas lacunas: se o seu aplicativo abre PDF, abra o arquivo em `02-projetos-pdf` e olhe; se não abre, deixe como lacuna.
- **Imagens.** O pipeline monta `04-transcricoes/folhas-de-contato/folha-NN.jpg`: cada folha tem 12 miniaturas numeradas (fotos e um quadro de cada vídeo), com o nome do arquivo e a data da mensagem que o anexou. "(nome do arquivo)" ao lado da data quer dizer que nenhuma mensagem cita o arquivo e a data veio do nome: confira antes de usar. O `indice.json` da mesma pasta liga cada número ao arquivo. Olhe todas as folhas. Se o seu aplicativo permitir subagentes, distribua as folhas entre eles em paralelo, mesmo usando um modelo mais simples: cada um devolve só as imagens que mostram um fato da obra (trinca, base sem acabamento, frente sem liberação, peça instalada, desenho técnico), com o número, a data e o fato em uma frase. A descrição é para você, não para o relatório. Sem subagentes, olhe as folhas você mesmo. Se uma miniatura parecer importante e pequena demais, abra o arquivo original em `03-midias`.
- **Outros formatos.** Arquivo que o computador não lê (desenho `.dwg`, cartão de contato `.vcf`, planilha `.xls` antiga) fica em `01-conversas/outros` ou aparece nas lacunas. Cartão de contato ajuda a saber quem é quem; desenho que você não consegue abrir fica como lacuna.
- **Arquivos fora da exportação.** O WhatsApp não exporta tudo. Mensagem `<Mídia oculta>` é arquivo que não veio no zip: o nome pode aparecer, o conteúdo não. Não deduza o conteúdo pelo nome.

### 4.2 Registrar no `analise.json`

O relatório é curto, no formato do relatório aprovado (8665.1 V3): uma tabela de fatos por etapa, uma leitura curta, a análise de prazos, o diagnóstico em tópicos e a conclusão. Todo o material que você leu serve para escrever isso bem, não para entrar inteiro no Word. Não copie mensagem, transcrição ou descrição de imagem para o relatório.

1. **Fatos.** Para cada fato real que faltou, acrescente em `eventos_adicionais`:

```json
{"data": "2026-01-13", "hora": "10:30", "etapa": "C", "autor": "Nome", "ocorrencia": "Medição in loco realizada na cozinha.", "impacto": "", "destaque": ""}
```

`ocorrencia` é uma frase objetiva, de até 25 palavras, como nas tabelas do relatório aprovado ("Medição da piscina não realizada: área sem liberação."). Em obra com várias frentes (banhos, piscina, cozinha), comece pela frente: "Banho Master: retirado da produção para modificação." `data`, `hora` e `autor` são os da mensagem, copiados do `.txt`: a conferência do passo 4.3 compara com a conversa. `impacto` só vale na etapa J. Etapa é uma letra de A a J ou L. Fato que veio de mídia leva `midias` com o arquivo e a marca da fonte na ocorrência: "[fonte: áudio transcrito, conferir]", "[fonte: vídeo transcrito, conferir]" ou "[fonte: foto, conferir]" (a marca não aparece no Word).
Programado não é feito. Mensagem que só programa, agenda ou pede o fato ("entrega programada para amanhã", "pedido de visita para aprovar as chapas") leva `"programado": true`: a linha fica na tabela da etapa, mas não vira marco, não entra no Quadro-Resumo nem no confronto com o contrato. O script já marca sozinho as mensagens das etapas A, C, H, I e L com "programado", "agendado", "agendamento", "previsto" ou "para amanhã"; confira e desmarque com `ajustes_eventos` (`"programado": false`) quando o fato de fato aconteceu. Fato realizado que não é o marco do ciclo (reposição de peças, peça extra, segunda instalação) leva `"marco": false`: fica na tabela da etapa, mas não vira a primeira entrega ou a entrada da equipe da frente. Quando a mensagem conta um fato de outro dia ("aprovados pessoalmente em 23/09", escrita em 24/09), mantenha `data` e `hora` da mensagem e acrescente `"data_evento": "2025-09-23"`: os marcos usam a data do fato. Procure no grupo a confirmação de cada fato programado (entrega feita, equipe na obra) e registre a confirmação como fato próprio.
Obra multifrente. Quando os ambientes têm ciclos próprios (banhos, living, piscina; bancadas de fases diferentes como "Bancadas 1ª fase" e "Bancadas 2ª fase"), acrescente `"frente": "Banhos"` em cada fato de medição, projeto, aprovação, entrega, instalação e conclusão daquela frente, sempre com o mesmo nome. A Análise de Prazos passa a medir os intervalos dentro de cada frente (aprovação dos banhos → entrega dos banhos), como no relatório aprovado, e não encadeia frentes diferentes. Para cada frente, procure as datas de fim de ciclo (entrega, entrada da equipe, fim da instalação, conclusão): a Análise de Prazos mostra como "pendente, dado não identificado" a próxima data que não estiver registrada. Fato da obra toda fica sem `frente`. Num fato lido do grupo, use `ajustes_eventos` (`"frente": "Banhos"`). A remontagem imprime `Aviso de frente: ...` para fato de aprovação, entrega, instalação ou conclusão sem frente numa obra multifrente e para prazo com frente que não existe nos fatos: resolva cada um. Interferência (etapa J) nunca entra como passo na Análise de Prazos.
2. **Corrigir ou tirar.** Use `ajustes_eventos` com `{"data": "2026-01-13", "hora": "10:30", "etapa_original": "J", "remover": true}`. Para trocar a etapa, use `"etapa": "C"`; para encurtar o texto, `"ocorrencia": "..."`.
Etapa J por tipo. Como no relatório aprovado (J.1 dependências civis e de terceiros, J.2 a frente mais crítica, J.3 logística e quebras, J.4 comercial e administrativo), dê a cada interferência um `"grupo"` com o nome do tipo, sempre igual ("Civil e terceiros", "Banho Master: base e banheira (frente mais crítica)", "Logística"). O Word faz uma tabela por tipo, na ordem do primeiro fato. Quando a mensagem mostra a equipe da Armanilux na obra sem poder trabalhar (sem frente, dispensada, deslocada à toa), acrescente `"dias_sem_frente"` com os dias perdidos que o grupo permite contar (em geral 1 por data; parada longa contada numa mensagem só, o número de dias úteis dela); o Word soma no fim da etapa J, contando cada data uma vez. Sem contagem possível, não ponha o campo. No `impacto`, diga o efeito em dias quando o grupo permite ("1 dia de equipe sem frente", "medição adiada 5 d.u."), não só "equipe parada".
3. **Cor da linha.** `destaque` pinta a linha como no relatório aprovado: `"reprocesso"` (salmão: revisão, refação, peça quebrada, mudança após aprovação) ou `"ocioso"` (amarelo: espera, medição não realizada, frente não liberada, pendência que se arrasta). O script já sugere uma cor (`destaque_auto`; toda linha da etapa E sai salmão, porque é pedido de revisão); confira e troque com `destaque` no evento adicional ou em `ajustes_eventos`. `"nenhum"` tira a cor. Destaque só o que a pessoa precisa ver.
4. **Conclusão.** A obra só aparece como concluída (Quadro-Resumo e tabela de marcos) com um fato da etapa L marcado `"conclusao": true`: a mensagem que registra o fim dos serviços e a validação final (aceite, termo assinado, "obra entregue"). Reclamação ou reparo ficam na etapa L sem essa marca. O fim de uma frente ("Banhos concluídos") leva `"conclusao": true` com a `frente`: fecha o ciclo daquela frente na Análise de Prazos, não a obra. Sem fato marcado, o Word diz "dado não identificado (pendente)". Num fato lido do grupo, marque com `ajustes_eventos` (`"conclusao": true`). Com mais de um fato marcado, vale a data do último.
5. **Imagens.** Olhe as imagens só para entender a obra. Se uma imagem mostra um fato datado (trinca, base sem acabamento, frente sem liberação, peça instalada), registre o fato em `eventos_adicionais` com a data da foto e "[fonte: foto, conferir]". Não escreva descrição de imagem para o relatório.
6. **Prazo contratual.** Obrigatório procurar no grupo e nos documentos (orçamento, proposta, contrato, cronograma, mensagem de regras do grupo) prazos declarados, como "medição até 6 dias úteis após a solicitação". Só o que estiver escrito: não deduza. Para cada prazo, acrescente em `prazos_contratuais`:

```json
{"descricao": "Projeto executivo até 6 d.u. da medição", "de": "C", "para": "D", "limite_du": 6, "fonte": "Orçamento 1001.2, enviado no grupo em 17/06/2026", "fonte_data": "2026-06-17"}
```

`fonte_data` é obrigatório: a data em que a regra apareceu no grupo (mensagem ou envio do documento), não a data impressa em outro lugar. A regra que vale para um período é a que já estava escrita quando o período começou:

- Use a fonte mais recente escrita **antes** do início do período. Documento enviado depois do período (por exemplo, o orçamento de um serviço novo) não prova a regra daquela época.
- Se duas fontes dizem coisas diferentes ("5 dias" num documento, "5 dias úteis" numa mensagem), vale a da época; a unidade (dias úteis ou corridos) vem dela. Cite a outra em `fonte` só se ajudar.
- Se a única fonte é posterior ao início do período, mantenha o prazo só se o documento o apresenta como regra geral (por exemplo, a lista padrão de prazos do orçamento), não como prazo daquele serviço novo; o Word marca o prazo com * e explica embaixo da tabela. Nunca troque a fonte por uma posterior para mudar o resultado.
- A remontagem imprime `Aviso de prazo: ...` para fonte posterior ao início ou sem `fonte_data`. Resolva cada aviso (procure uma fonte anterior) ou conte na resposta final por que ficou.

`de` e `para` são as etapas cujo primeiro registro marca o início e o fim do prazo. Quando a obra tem várias frentes e você mediu um ciclo específico (por exemplo, a aprovação e a entrega da piscina), use `"inicio"` e `"fim"` (AAAA-MM-DD) no lugar de `de` e `para`, e diga a frente na descrição. Prazo em faixa ("20 a 25 d.u.") usa o limite maior. Prazo escrito só em "dias", sem "úteis", conta dias corridos: acrescente `"unidade": "dias_corridos"` (o número continua em `limite_du`). Sem `unidade`, vale dias úteis. O script calcula o realizado e pinta de vermelho o que passou do prazo. Se o fim do período só foi programado ("início da entrega programado para 10/11") e nenhuma mensagem confirma, acrescente `"programado": true` no prazo: o Word mostra "programado, sem confirmação" e o prazo não conta como cumprido nem como estourado. Não escreva nos textos que esse prazo foi cumprido. Sem prazo declarado, deixe a lista vazia e escreva em `lacunas_adicionais` "Prazo contratual não declarado no grupo nem nos documentos.". Em obra com várias frentes, ponha `"frente"` no prazo junto com `de` e `para` (o script usa só os fatos dessa frente) ou use `inicio` e `fim`: o primeiro registro de uma etapa na obra inteira pode ser de outra frente e dar um número enganoso.
7. **Pendências e obra.** Confira `pendencias` e os campos de `obra`. `pendencias_revisadas` traz só as pendências reais (`{"item": "...", "status": "Pendente"}`); `obra_ajustes` traz `construtora`, `engenheiro`, `arquitetura`, `responsavel_armanilux` e `endereco` quando o grupo não traz em formato fixo.
8. **Lacunas.** `lacunas_automaticas` já traz o que o computador sabe que não leu. Acrescente em `lacunas_adicionais` o que você percebeu (etapa sem registro, documento citado e nunca enviado, decisão tomada fora do grupo), uma frase curta por lacuna. Elas entram na Nota Metodológica. Não deduza o conteúdo de arquivo que não veio na exportação (`arquivos_fora_da_exportacao`).
9. **Textos do relatório.** Escreva, com fatos do grupo e datas, e curto:
   - `comentarios.<etapa>.introducao`: uma ou duas linhas antes da tabela, só quando ajudam ("A aprovação de chapas ocorreu de forma fracionada.").
   - `comentarios.<etapa>.leitura`: a "Leitura da Etapa", até três frases, com o intervalo que importa em dias úteis. Sem leitura, o Word mostra só o período da etapa.
   - `diagnostico_prompt`: `{"reprocessos": [...], "tempos_ociosos": [...], "atrasos_internos": [...], "dependencias_externas": [...], "interferencias": [...]}`, cada um uma lista de tópicos curtos com data. `interferencias` é o impacto da etapa J no cronograma e na produtividade: um tópico por tipo de interferência e, se houver, o total de dias de equipe sem frente.
   - `pontos_criticos`: lista numerada dos principais pontos críticos de atraso.
   - `impactos_prazo`: um parágrafo sobre o impacto no prazo final (duração em dias úteis e corridos; confronto com o prazo contratual, se houver).
   - `conclusao_personalizada`: o diagnóstico da eficiência do fluxo operacional, um ou dois parágrafos.
   - `recomendacoes_personalizadas`: lista de recomendações práticas, sem o número na frente.

O que o grupo não sustenta fica `dado não identificado`. Não crie etapa K. Postura do texto: formal, neutra, a favor do registro da Armanilux, sem acusar pessoa. Intervalo em dias úteis não é atraso atribuído. Reprocesso, espera e dependência de obra (marcenaria, contrapiso, ponto hidráulico, medição pendente) aparecem separados.

### 4.3 Remontar

Remonte o Word com o comando do passo 5. Toda remontagem grava `04-transcricoes/verificacao.md`: o script confere cada fato contra a conversa (mesmo dia, mesma hora, mesmo primeiro nome do autor) ou contra a mídia citada (arquivo transcrito ou presente na pasta da obra), e lista o que não bateu. Fato sem autor e sem hora não tem como ser conferido: preencha os dois. Corrija cada item da lista no `analise.json` ou tire o fato. Remonte até a lista ficar vazia.

### 4.4 Conferência independente

A conferência do script só vê data, hora e autor. Ela não vê se o texto diz o que a mensagem diz. Antes de dar o relatório por revisado, faça uma conferência de conteúdo por alguém que não escreveu o texto:

- Se o seu aplicativo permitir subagentes, abra um subagente novo, sem o contexto desta conversa. Entregue a ele só os caminhos de `analise.json`, do `.txt` da conversa, de `02-projetos-pdf`, de `03-midias` e de `04-transcricoes` (com as folhas de contato), com esta tarefa: "Para cada fato em `eventos` e cada frase de `comentarios`, `diagnostico_prompt`, `pontos_criticos`, `impactos_prazo`, `conclusao_personalizada`, `recomendacoes_personalizadas`, `prazos_contratuais`, `obra_ajustes`, `pendencias_revisadas` e `lacunas_adicionais`, ache no material a mensagem, transcrição, documento ou imagem que sustenta o que está escrito. Responda, item por item: sustentado (com data, hora e autor da fonte), não sustentado, ou diferente do que a fonte diz (com o que a fonte diz). Para cada item de `prazos_contratuais`, diga também se a fonte foi escrita no grupo antes do início do período medido e se alguma mensagem anterior dá outro número ou outra unidade (dias úteis ou corridos). Não corrija nada."
- Sem subagentes, faça você mesmo uma segunda passada, item por item, procurando cada fato no `.txt`.

Corrija ou tire tudo o que voltar como não sustentado ou diferente. O que não der para confirmar vira lacuna em `lacunas_adicionais`, não afirmação.

### 4.5 Marcar como revisado

Só depois de 4.1 a 4.4, grave `"revisado": true` no `analise.json` e remonte. Sem isso o Word sai com a faixa vermelha "RASCUNHO NÃO REVISADO" no topo, de propósito, para ninguém enviar um relatório sem conferência. Se `verificacao.md` ainda listar fatos que não batem, ou se a conferência não rodou, o script grava rascunho mesmo com `"revisado": true` e diz por quê: volte ao 4.3.

A versão final tem o mesmo número do rascunho: na primeira vez, `v1`. Remontar depois disso (inclusive com `--mostrar`, ou para corrigir um erro) regrava o mesmo `vN`, sem criar `v2`. Se o Word estiver aberto, o script pede para fechar o arquivo: feche e remonte.

## 5. Remontar o Word

Depois de editar o JSON:

```bash
PYTHON SKILL/scripts/run_pipeline.py --rebuild-only --recalcular --obra-dir "PASTA-DA-OBRA"
```

`--recalcular` refaz dias úteis, marcos, cores sugeridas e o confronto com o prazo contratual a partir dos eventos corrigidos. Os textos escritos na revisão são mantidos.

Na última remontagem, a que vai para a pessoa, acrescente `--mostrar`: o script abre a pasta da obra com o Word já selecionado. Todo comando que grava o Word imprime uma linha `RELATORIO_WORD: <caminho>`; é por ela que você acha o arquivo. Quando sai PDF, vem também `RELATORIO_PDF: <caminho>`. Com entrega por link, a versão revisada imprime `RELATORIO_LINK: <caminho>`, a cópia na pasta da nuvem.

Não entregue um Word escrito à mão por fora do script. O arquivo versionado (`v1`, `v2`, …) é o que a pessoa abre. `v2` só existe quando chegou uma conversa nova da obra.

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
