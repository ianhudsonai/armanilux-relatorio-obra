# Revisão da análise

Como fazer o passo 4 do `SKILL.md`. Leia este arquivo inteiro antes de abrir o `analise.json`. Os nomes e formatos de cada campo estão em `analise-json.md`.

A leitura automática é só um rascunho: num grupo grande ela deixa etapas vazias (chapas, medição, entrega, conclusão) e pode classificar errado. Leia todo o material para entender a obra por completo; escreva um relatório curto e correto. Tudo o que entra precisa estar no grupo: numa mensagem, numa transcrição, num documento ou numa imagem. O que você não conseguiu ler ou confirmar não some: vira lacuna, numa frase curta.

## Ler em partes

Num grupo grande, o material não cabe numa leitura só, e o que não cabe some sem aviso: no Codex, um comando que mostra mais de ~10 KB ou 256 linhas perde o meio. Por isso o pipeline divide tudo em partes pequenas (até ~8.000 caracteres e 150 linhas, juntando dias inteiros) em `04-transcricoes/leitura/`:

- `conversa-NNN.txt`: a conversa, em ordem, cada mensagem como `[DD/MM/AAAA HH:MM] Autor: texto`, com a ordem dia/mês já decidida. "(data incerta: …)" no fim quer dizer que dia e mês podem estar trocados.
- `transcricoes-NNN.txt`: cada áudio ou vídeo transcrito, com a data, a hora e o autor da mensagem que o anexou.
- `documento-NNN.txt`: o texto de cada documento, em partes.

`04-transcricoes/revisao-progresso.md` lista essas partes e as folhas de contato, uma linha `- [ ]` cada. Como trabalhar:

1. Leia uma parte por comando, inteira, por exemplo `Get-Content -Raw -Encoding UTF8 "<caminho da parte>"`. Se a saída disser que linhas foram cortadas ou omitidas, leia de novo em duas metades (`-TotalCount 75` e depois `| Select-Object -Skip 75`). Para ler o material, use as partes, não o `.txt` original nem o `analise.json`.
2. Logo depois de cada parte, registre no `analise.json` os fatos dela (4.2) e troque `[ ]` por `[x]` na linha da parte. O que ainda não é fato (quem é quem, prazo citado, dúvida, ideia para os textos) vai na seção Notas, no fim do mesmo arquivo. Assim nada se perde se a conversa for resumida ou cortada. Enquanto o pipeline ainda roda (a transcrição, na primeira vez), não edite o `analise.json`, porque ele é regravado no fim: anote os fatos em Notas e passe para o `analise.json` quando o comando terminar.
3. Não marque parte que não leu inteira. Cada remontagem imprime `LEITURA: X de Y partes lidas`, e a versão final só sai com todas marcadas.
4. Ao continuar (depois de um "continue" ou num chat novo), abra `revisao-progresso.md`, releia as Notas e siga da primeira linha sem `[x]`.

O `analise.json` é grande: não abra o arquivo inteiro. Para editar, use um script Python curto que lê o JSON, muda só os campos da revisão e grava em UTF-8 (`ensure_ascii=False`).

Com subagentes (o Codex e o Claude Code têm; tente primeiro): distribua as partes sem `[x]` entre eles, algumas por subagente, e as folhas de contato também, mesmo com um modelo mais simples. Cada um devolve, por parte: os fatos de cada etapa com data, hora, autor e o trecho exato; as pendências; quem é quem (empresa, função); nas folhas, só as imagens que mostram um fato da obra, com o número, a data e o fato em uma frase. Você registra e marca as partes. Se o aplicativo recusar subagentes, leia você mesmo, na ordem da lista.

## 4.1 Ler todo o material

Leia tudo antes de escrever: cada linha de `revisao-progresso.md`. Não basta a lista de candidatos.

- **Conversa inteira.** Todas as partes `conversa-NNN.txt`, da primeira à última. `04-transcricoes/candidatos-por-etapa.md` serve de índice, não de limite.
- **Mensagens coladas.** No `.txt` original, mensagem de outra conversa colada no grupo aparece como uma linha dentro da mensagem de quem colou, no formato `[12:25, 03/07/2026] Nome: texto` ou `[03/07, 12:25] Nome: texto`; na parte de leitura ela já vem como linha própria, com "(colada no grupo por … em …)". A data, a hora e o autor do fato são os dessa linha (os originais); quem colou e quando é a mensagem em volta. No `analise.json`, o fato que veio de uma colada termina com "(encaminhada no grupo por … em …)".
- **Áudios e vídeos.** Todas as partes `transcricoes-NNN.txt`, não só o que parece relevante. Vídeo muitas vezes é o registro de uma visita ou de uma medição e traz a data e o fato que faltam no texto.
- **Documentos.** Todas as partes `documento-NNN.txt` (projetos, folhas de medição, cronogramas, memoriais). Documento sem texto (desenho técnico) aparece nas lacunas: se o seu aplicativo abre PDF, abra o arquivo em `02-projetos-pdf` e olhe; se não abre, deixe como lacuna.
- **Imagens.** O pipeline monta `04-transcricoes/folhas-de-contato/folha-NN.jpg`: cada folha tem 12 miniaturas numeradas (fotos e um quadro de cada vídeo), com o nome do arquivo e a data da mensagem que o anexou. "(nome do arquivo)" ao lado da data quer dizer que nenhuma mensagem cita o arquivo e a data veio do nome: confira antes de usar. O `indice.json` da mesma pasta liga cada número ao arquivo. Olhe todas as folhas, uma por vez, e marque cada uma em `revisao-progresso.md`. Se uma miniatura parecer importante e pequena demais, abra o arquivo original em `03-midias`.
- **Outros formatos.** Arquivo que o computador não lê (desenho `.dwg`, cartão de contato `.vcf`, planilha `.xls` antiga) fica em `01-conversas/outros` ou aparece nas lacunas. Cartão de contato ajuda a saber quem é quem; desenho que você não consegue abrir fica como lacuna.
- **Arquivos fora da exportação.** O WhatsApp não exporta tudo. Mensagem `<Mídia oculta>` é arquivo que não veio no zip: o nome pode aparecer, o conteúdo não. Não deduza o conteúdo pelo nome.

Pronto quando: toda linha de `revisao-progresso.md` está com `[x]` e os fatos de cada parte estão no `analise.json`.

## 4.2 Registrar no `analise.json`

O relatório é curto, no formato do relatório aprovado (8665.1 V3): uma tabela de fatos por etapa, uma leitura curta, a análise de prazos, o diagnóstico em tópicos e a conclusão. Todo o material que você leu serve para escrever isso bem, não para entrar inteiro no Word. Não copie mensagem, transcrição ou descrição de imagem para o relatório.

### Fatos

Para cada fato real que faltou, acrescente em `eventos_adicionais`:

```json
{"data": "2026-01-13", "hora": "10:30", "etapa": "C", "autor": "Nome", "ocorrencia": "Medição in loco realizada na cozinha.", "impacto": "", "destaque": ""}
```

`ocorrencia` é uma frase objetiva, de até 25 palavras, como nas tabelas do relatório aprovado ("Medição da piscina não realizada: área sem liberação."). Em obra com várias frentes (banhos, piscina, cozinha), comece pela frente: "Banho Master: retirado da produção para modificação." `data`, `hora` e `autor` são os da mensagem, copiados do `.txt`: a conferência do passo 4.3 compara com a conversa. `impacto` só vale na etapa J. Etapa é uma letra de A a J ou L. Fato que veio de mídia leva `midias` com o arquivo e a marca da fonte na ocorrência: "[fonte: áudio transcrito, conferir]", "[fonte: vídeo transcrito, conferir]" ou "[fonte: foto, conferir]" (a marca não aparece no Word).

Para corrigir ou tirar um fato que a leitura automática achou, use `ajustes_eventos` com `{"data": "2026-01-13", "hora": "10:30", "etapa_original": "J", "remover": true}`. Para trocar a etapa, use `"etapa": "C"`; para encurtar o texto, `"ocorrencia": "..."`. As marcas abaixo (`programado`, `marco`, `frente`, `conclusao`…) entram num fato lido do grupo do mesmo jeito, por `ajustes_eventos`.

### Programado, marco e data do fato

Programado não é feito. Mensagem que só programa ou agenda um fato futuro ("entrega programada para amanhã", "visita agendada para quarta") leva `"programado": true`: a linha fica na tabela da etapa com "(programado)", mas não vira marco, não entra no Quadro-Resumo nem no confronto com o contrato. O script já marca sozinho as mensagens das etapas A, C, H, I e L com "programado", "agendado", "agendamento", "previsto" ou "para amanhã"; confira e desmarque com `ajustes_eventos` (`"programado": false`) quando o fato de fato aconteceu. Procure no grupo a confirmação de cada fato programado (entrega feita, equipe na obra) e registre a confirmação como fato próprio.

Ação que aconteceu mas não é o marco (cobrança, pedido, checklist enviado, "medição não realizada", reposição de peças, peça extra, segunda instalação) leva `"marco": false`, não `"programado"`: fica na tabela da etapa sem "(programado)" e não vira a aprovação, a primeira entrega ou a entrada da equipe da frente. A remontagem imprime `Aviso de programado: ...` quando um fato marcado como programado conta uma ação feita: troque a marca. Liberação de frente ("piso liberado para instalação") não é entrada da equipe: a entrada é o primeiro dia em que a equipe trabalhou de fato.

Quando a mensagem conta um fato de outro dia ("aprovados pessoalmente em 23/09", escrita em 24/09), mantenha `data` e `hora` da mensagem e acrescente `"data_evento": "2025-09-23"`: os marcos usam a data do fato. Quando o grupo só mostra que o fato aconteceu entre duas datas (entrega programada para 10/03; em 12/03, "na última entrega"; equipe sem frente em 04/05 e trabalhando em 11/05), não escolha uma data: ponha `"data_evento"` no primeiro dia possível e `"data_evento_ate"` no último. O Word diz "fato entre 10/03 e 12/03", o Quadro-Resumo mostra a faixa e os dias úteis saem em faixa ("30–32 d.u.").

### Aprovação revista

Registre cada aprovação do grupo na etapa G, inclusive a que foi revista depois. O script usa como marco da frente a aprovação que valeu: quando a uma aprovação seguem revisão (E ou F) e nova aprovação da mesma frente, vale a nova; mudança depois da última aprovação (já na produção) não desfaz a aprovação. Por isso registre também cada pedido de revisão (E) e cada envio revisado (F) com a `frente`. A remontagem imprime `Aprovação revista: ...` e o Word diz quais foram revistas. Se a revisão foi pequena e a primeira aprovação valeu, marque a nova com `"marco": false`.

### Obra multifrente

Quando os ambientes têm ciclos próprios (banhos, living, piscina; bancadas de fases diferentes como "Bancadas 1ª fase" e "Bancadas 2ª fase"), acrescente `"frente": "Banhos"` em cada fato de medição, projeto, aprovação, entrega, instalação e conclusão daquela frente, sempre com o mesmo nome. A Análise de Prazos passa a medir os intervalos dentro de cada frente (aprovação dos banhos → entrega dos banhos), como no relatório aprovado, e não encadeia frentes diferentes. Para cada frente, procure as datas de fim de ciclo (entrega, entrada da equipe, fim da instalação, conclusão): a Análise de Prazos mostra como "pendente, dado não identificado" a próxima data que não estiver registrada. Fato da obra toda fica sem `frente`.

A remontagem imprime `Aviso de frente: ...` para fato de aprovação, entrega, instalação ou conclusão sem frente numa obra multifrente, para marco com data fora da ordem do ciclo (fica fora da Análise de Prazos) e para prazo com frente que não existe nos fatos: resolva cada um. Na Análise de Prazos, os passos são só os marcos do ciclo (chapas, medição, preliminar, aprovação, entrega, equipe, conclusão), na ordem; pedido de visita, revisões e interferências ficam nas suas etapas.

### Etapa J por tipo e dias perdidos

Como no relatório aprovado (J.1 dependências civis e de terceiros, J.2 a frente mais crítica, J.3 logística e quebras, J.4 comercial e administrativo), dê a cada interferência um `"grupo"` com o nome do tipo, sempre igual ("Civil e terceiros", "Banho Master: base e banheira (frente mais crítica)", "Logística"). O Word faz uma tabela por tipo, na ordem do primeiro fato.

Quando a mensagem mostra a equipe da Armanilux na obra sem poder trabalhar (sem frente, dispensada, deslocada à toa), acrescente `"dias_sem_frente"` com os dias perdidos que o grupo permite contar (em geral 1 por data; parada longa contada numa mensagem só, o número de dias úteis dela); o Word soma no fim da etapa J, contando cada data uma vez. Sem contagem possível, não ponha o campo. Dia em que a equipe fez outro serviço a pedido da obra (mudou peças de lugar, por exemplo) não é dia sem frente. Conte também o outro lado: dia perdido por causa da Armanilux (entrega adiada por imprevisto, instalador doente, veículo quebrado, equipe atrasada) é um fato da etapa J com `"dias_perdidos_armanilux"` (em geral 1 por data); o Word soma ao lado dos dias sem frente. No `impacto`, diga o efeito em dias quando o grupo permite ("1 dia de equipe sem frente", "medição adiada 5 d.u."), não só "equipe parada".

### Cor da linha

`destaque` pinta a linha como no relatório aprovado: `"reprocesso"` (salmão: revisão, refação, peça quebrada, mudança após aprovação) ou `"ocioso"` (amarelo: espera, medição não realizada, frente não liberada, pendência que se arrasta). O script já sugere uma cor (`destaque_auto`; toda linha da etapa E sai salmão, porque é pedido de revisão); confira e troque com `destaque` no evento adicional ou em `ajustes_eventos`. `"nenhum"` tira a cor. Destaque só o que a pessoa precisa ver.

### Conclusão

A obra só aparece como concluída (Quadro-Resumo e tabela de marcos) com um fato da etapa L marcado `"conclusao": true`: a mensagem que registra o fim dos serviços e a validação final (aceite, termo assinado, "obra entregue"). Reclamação ou reparo ficam na etapa L sem essa marca. O fim de uma frente ("Banhos concluídos") leva `"conclusao": true` com a `frente`: fecha o ciclo daquela frente na Análise de Prazos, não a obra. Sem fato marcado, o Word diz "dado não identificado (pendente)". Com mais de um fato marcado, vale a data do último.

### Imagens

Olhe as imagens só para entender a obra. Se uma imagem mostra um fato datado (trinca, base sem acabamento, frente sem liberação, peça instalada), registre o fato em `eventos_adicionais` com a data da foto e "[fonte: foto, conferir]".

### Prazo contratual

Obrigatório procurar no grupo e nos documentos (orçamento, proposta, contrato, cronograma, mensagem de regras do grupo) prazos declarados, como "medição até 6 dias úteis após a solicitação". Só o que estiver escrito: não deduza. Para cada prazo, acrescente em `prazos_contratuais`:

```json
{"descricao": "Projeto executivo até 6 d.u. da medição", "de": "C", "para": "D", "limite_du": 6, "fonte": "Orçamento 1001.2, enviado no grupo em 17/06/2026", "fonte_data": "2026-06-17"}
```

`fonte_data` é obrigatório: a data em que a regra apareceu no grupo (mensagem ou envio do documento), não a data impressa em outro lugar. A regra que vale para um período é a que já estava escrita quando o período começou:

- Use a fonte mais recente escrita **antes** do início do período. Documento enviado depois do período (por exemplo, o orçamento de um serviço novo) não prova a regra daquela época.
- Se duas fontes dizem coisas diferentes ("5 dias" num documento, "5 dias úteis" numa mensagem), vale a da época; a unidade (dias úteis ou corridos) vem dela. Cite a outra em `fonte` só se ajudar.
- Se a única fonte é posterior ao início do período, mantenha o prazo só se o documento o apresenta como regra geral (por exemplo, a lista padrão de prazos do orçamento), não como prazo daquele serviço novo; o Word marca o prazo com * e explica embaixo da tabela. Nunca troque a fonte por uma posterior para mudar o resultado.
- A remontagem imprime `Aviso de prazo: ...` para fonte posterior ao início ou sem `fonte_data`. Resolva cada aviso (procure uma fonte anterior) ou conte na resposta final por que ficou.

`de` e `para` são as etapas cujo primeiro registro marca o início e o fim do prazo. Quando a obra tem várias frentes e você mediu um ciclo específico (por exemplo, a aprovação e a entrega da piscina), use `"inicio"` e `"fim"` (AAAA-MM-DD) no lugar de `de` e `para`, e diga a frente na descrição. Em obra com várias frentes, ponha `"frente"` no prazo junto com `de` e `para` (o script usa só os fatos dessa frente) ou use `inicio` e `fim`: o primeiro registro de uma etapa na obra inteira pode ser de outra frente e dar um número enganoso.

Prazo em faixa ("20 a 25 d.u.") usa o limite maior. Prazo escrito só em "dias", sem "úteis", conta dias corridos: acrescente `"unidade": "dias_corridos"` (o número continua em `limite_du`). Sem `unidade`, vale dias úteis. O script calcula o realizado e pinta de vermelho o que passou do prazo.

Se o fim do período só foi programado ("início da entrega programado para 10/11") e nenhuma mensagem confirma, acrescente `"programado": true` no prazo: o Word mostra "programado, sem confirmação" e o prazo não conta como cumprido nem como estourado. Não escreva nos textos que esse prazo foi cumprido. Fim (ou início) sem dia exato no grupo: `"fim"` no primeiro dia possível e `"fim_ate"` no último (`"inicio_ate"` para o início); o Word mostra a faixa de dias e não afirma estouro quando só o fim da faixa passa do limite.

Quando o período passou do limite porque se esperava o outro lado (aval da arquitetura para começar, frente não liberada, decisão da cliente), escreva em `"quem_segurou"` uma frase curta com a data ("Arquitetura: aval para iniciar só em 10/03, 15:00; preliminar enviado no mesmo dia") e acrescente `"externo": true`: o Word mostra a coluna "Quem segurou" e não conta esse prazo como atraso da Armanilux. Quando a espera era da Armanilux, escreva `quem_segurou` sem `externo`.

Sem prazo declarado, deixe a lista vazia e escreva em `lacunas_adicionais` "Prazo contratual não declarado no grupo nem nos documentos.".

### Pendências e obra

Confira `pendencias` e os campos de `obra`. `pendencias_revisadas` traz só as pendências reais (`{"item": "...", "status": "Pendente"}`); `obra_ajustes` traz `construtora`, `engenheiro`, `arquitetura`, `responsavel_armanilux` e `endereco` quando o grupo não traz em formato fixo.

### Lacunas

`lacunas_automaticas` já traz o que o computador sabe que não leu. Acrescente em `lacunas_adicionais` o que você percebeu (etapa sem registro, documento citado e nunca enviado, decisão tomada fora do grupo), uma frase curta por lacuna. Elas entram na Nota Metodológica. Não deduza o conteúdo de arquivo que não veio na exportação (`arquivos_fora_da_exportacao`).

### Textos do relatório

Escreva, com fatos do grupo e datas, e curto:

- `comentarios.<etapa>.introducao`: uma ou duas linhas antes da tabela, só quando ajudam ("A aprovação de chapas ocorreu de forma fracionada.").
- `comentarios.<etapa>.leitura`: a "Leitura da Etapa", até três frases, com o intervalo que importa em dias úteis. Sem leitura, o Word mostra só o período da etapa.
- `comentarios.<etapa>.status`: o veredito da etapa em uma linha, com o que está comprovado e o que não está ("visita programada para 25/09; realização efetiva – dado não identificado", "aprovação do cliente em 22/10; assinatura digital – dado não identificado"). Escreva em toda etapa com fato. Sem status, o Word só escreve um para etapa que tem apenas fato programado.
- `interpretacao_intervalos`: o que cada intervalo da Análise de Prazos quer dizer, em poucas palavras, sem culpar ninguém: `[{"de": "G", "para": "H", "frente": "Banhos", "texto": "Produção e logística."}]` (`frente` só em obra multifrente). Exemplos: "Desenvolvimento rápido", "Intervalo sem comprovação de avanço no grupo", "Espera pelo executivo da marcenaria". Com pelo menos uma, o Word ganha a coluna "Interpretação".
- `diagnostico_temas`: abre o diagnóstico com uma tabela de 3 a 6 temas: `[{"tema": "Projeto executivo da marcenaria", "avaliacao": "Gargalo documentado", "leitura": "Executivo recebido só em 20/10; a compatibilização dependia dele."}]`. Em `avaliacao`, use uma destas: "Gargalo documentado", "Ponto crítico", "Comprovação incompleta", "Fluxo eficiente", "Não verificável". Outra avaliação segura a versão final. Inclua o que a Armanilux fez bem e o que fez mal.
- `diagnostico_prompt`: `{"reprocessos": [...], "tempos_ociosos": [...], "atrasos_internos": [...], "dependencias_externas": [...], "interferencias": [...]}`, cada um uma lista de tópicos curtos com data. Toda lista leva pelo menos um tópico: categoria sem registro no grupo leva uma frase como "Nenhum atraso da Armanilux registrado no grupo.". `interferencias` é o impacto da etapa J no cronograma e na produtividade: um tópico por tipo de interferência e, se houver, o total de dias de equipe sem frente.
- `pontos_criticos`: lista numerada dos principais pontos críticos de atraso.
- `impactos_prazo`: um parágrafo sobre o impacto no prazo final (duração em dias úteis e corridos; confronto com o prazo contratual, se houver).
- `conclusao_personalizada`: o diagnóstico da eficiência do fluxo operacional, um ou dois parágrafos.
- `recomendacoes_personalizadas`: recomendações práticas, cada uma com prioridade e resultado esperado: `[{"prioridade": "Alta", "medida": "Exigir o executivo da marcenaria antes de agendar a medição.", "resultado": "Evitar incompatibilidades."}]`. Prioridade "Alta", "Média" ou "Baixa". O Word faz a tabela Prioridade / Medida proposta / Resultado esperado. Lista só de frases (sem prioridade) ainda vale e sai numerada.
- `pontos_de_controle`: a sequência de liberações que evitaria os problemas desta obra, um item por ponto, cada um com o que conferir. Cada ponto responde a um problema desta obra que está no grupo (diga qual, com a data, na própria frase); ponto sem problema na obra fica de fora. Modelo para adaptar: "Liberação para medição: condições físicas e informações necessárias confirmadas"; "Liberação para projeto: executivos de terceiros recebidos e interfaces definidas"; "Liberação para produção: projeto aprovado formalmente"; "Liberação para entrega: acesso, recebimento e armazenamento confirmados"; "Liberação para instalação: frente, insumos e equipe confirmados"; "Encerramento: vistoria, pendências registradas e aceite final".

O que o grupo não sustenta fica `dado não identificado`. Postura do texto: formal, neutra, a favor do registro da Armanilux, sem acusar pessoa. O relatório só se defende se for justo com os dois lados: em `atrasos_internos`, liste os deslizes da própria Armanilux que o grupo mostra (desenho de produção com material errado, entrega adiada, instalador doente, medida não conferida); registre também quando o outro lado admite um erro (por exemplo, que deixou passar uma medida na aprovação) e quando contesta a Armanilux (por exemplo, num áudio do gestor da obra), com data. Intervalo em dias úteis não é atraso atribuído. Reprocesso, espera e dependência de obra (marcenaria, contrapiso, ponto hidráulico, medição pendente) aparecem separados.

Pronto quando: cada fato real do material está em `eventos` ou `eventos_adicionais`, cada prazo escrito está em `prazos_contratuais` (ou a lacuna diz que não há), e todos os textos da lista acima estão escritos.

## 4.3 Remontar até a conferência ficar vazia

Remonte o Word com o comando do passo 5 do `SKILL.md`. Toda remontagem grava `04-transcricoes/verificacao.md`: o script confere cada fato contra a conversa (mesmo dia, mesma hora, mesmo primeiro nome do autor) ou contra a mídia citada (arquivo transcrito ou presente na pasta da obra), e lista o que não bateu. Fato sem autor e sem hora não tem como ser conferido: preencha os dois. Corrija cada item da lista no `analise.json` ou tire o fato. Remonte até a lista ficar vazia. Resolva também cada `Aviso de programado`, `Aviso de frente` e `Aviso de prazo` que a remontagem imprimir.

## 4.4 Conferência independente

A conferência do script só vê data, hora e autor. Ela não vê se o texto diz o que a mensagem diz. Antes de dar o relatório por revisado, faça uma conferência de conteúdo por alguém que não escreveu o texto.

Cada remontagem refaz `04-transcricoes/conferencia.md`: uma linha `- [ ]` para cada fato de `eventos`, cada prazo de `prazos_contratuais` e cada frase dos textos do relatório (`comentarios`, `diagnostico_temas`, `interpretacao_intervalos`, `diagnostico_prompt`, `pontos_criticos`, `impactos_prazo`, `conclusao_personalizada`, `recomendacoes_personalizadas`, `pontos_de_controle`, `obra_ajustes`, `pendencias_revisadas`, `lacunas_adicionais`). Cada fato diz em que parte de `04-transcricoes/leitura/` procurar.

- Com subagentes (tente primeiro): abra um subagente novo, sem o contexto desta conversa. Entregue a ele só os caminhos de `conferencia.md`, de `04-transcricoes/leitura/`, das folhas de contato, de `02-projetos-pdf` e de `03-midias`, com esta tarefa: "Para cada linha de `conferencia.md`, ache no material a mensagem, transcrição, documento ou imagem que sustenta o que está escrito. Leia uma parte de `leitura/` por comando. Responda, item por item: sustentado (com data, hora e autor da fonte), não sustentado, ou diferente do que a fonte diz (com o que a fonte diz). Para cada prazo, diga também se a fonte foi escrita no grupo antes do início do período medido e se alguma mensagem anterior dá outro número ou outra unidade (dias úteis ou corridos). Não corrija nada." Com uma lista longa, divida as linhas entre alguns subagentes.
- Sem subagentes, faça você mesmo uma segunda passada, item por item, na ordem de `conferencia.md`: abra a parte indicada e ache a fonte. Não confie na memória da primeira leitura.

Marque `[x]` em cada item sustentado, e em cada item depois de corrigido, tirado ou virado lacuna em `lacunas_adicionais` (o que não der para confirmar vira lacuna, não afirmação). Item que você corrigiu volta sem marca na remontagem seguinte: confira de novo. Marque item por item, conforme avança, para continuar de onde parou depois de um "continue".

Ao terminar, registre no `analise.json` como a conferência foi feita: `"conferencia_independente": {"como": "subagente", "data": "2026-11-21"}` ou `{"como": "segunda passada", "data": "..."}`. Cada remontagem imprime `CONFERENCIA: X de Y itens`.

Pronto quando: todo item de `conferencia.md` está com `[x]` e `conferencia_independente` está gravado.

## 4.5 Marcar como revisado

Só depois de 4.1 a 4.4, grave `"revisado": true` no `analise.json` e remonte. Sem isso o Word sai com a faixa vermelha "RASCUNHO NÃO REVISADO" no topo, de propósito, para ninguém enviar um relatório sem conferência. O script grava rascunho mesmo com `"revisado": true`, e diz por quê, se `verificacao.md` ainda listar fatos que não batem, se a conferência não rodou (volte ao 4.3), se alguma parte de `revisao-progresso.md` ou item de `conferencia.md` estiver sem `[x]`, se faltar `conferencia_independente`, ou se faltar texto da revisão: as cinco listas de `diagnostico_prompt`, `pontos_criticos`, `conclusao_personalizada`, `recomendacoes_personalizadas`, e o prazo contratual (`prazos_contratuais` ou, em `lacunas_adicionais`, a frase "Prazo contratual não declarado no grupo nem nos documentos."). Escreva o que faltar (4.2) e remonte.

A versão final tem o mesmo número do rascunho: na primeira vez, `v1`. Remontar depois disso (inclusive com `--mostrar`, ou para corrigir um erro) regrava o mesmo `vN`, sem criar `v2`. Se o Word estiver aberto, o script pede para fechar o arquivo: feche e remonte.
