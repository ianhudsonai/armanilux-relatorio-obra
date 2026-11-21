# Formato do relatório

Português do Brasil, formal, técnico, neutro, sem emoji. Modelo: o relatório aprovado da obra 8665.1 V3 — curto, uma tabela de fatos por etapa, cores de destaque, análise de prazos, diagnóstico em tópicos e conclusão. O script `build_docx.py` já monta esta ordem. O relatório não é o lugar do contexto inteiro: o agente lê tudo para escrever pouco e certo.

## Capa

Título, obra e cliente, fornecedor, construtora, arquitetura, endereço, período, base documental, data de emissão e quem elaborou. Campo vazio vira `dado não identificado`.

## Nota Metodológica

Um parágrafo sobre a fonte (grupo, documentos, transcrições locais) e a regra do `dado não identificado`. Depois, em linhas com rótulo:

- Classificação usada: fato documentado, programado, dependência externa, dado não identificado e impacto potencial, cada um com uma frase.
- Limites do material: as lacunas, em frases curtas (arquivos que não vieram na exportação, documentos sem texto, áudios sem transcrição, o que a revisão anotou).
- Dias úteis: a convenção de contagem.
- Prazos contratuais de referência: só quando o grupo ou um documento informa, com a fonte.
- Convenção de cores: salmão = reprocesso ou retrabalho; amarelo = tempo ocioso, espera ou pendência; vermelho na Análise de Prazos = passou do prazo contratual informado ou, sem prazo informado, intervalo entre marcos acima de 20 dias úteis.

## Quadro-Resumo da Obra

Tabela Indicador | Valor: início do grupo, primeiros marcos realizados (chapas, medição, aprovação, entrega, instalação; programação não conta, vale a data do fato), último registro, duração em dias corridos e úteis, conclusão (só com fato da etapa L marcado `conclusao`; sem ele, "DADO NÃO IDENTIFICADO (pendente — ver Etapa L)"), prazo contratual.

## Etapas A a L

Cada etapa:

1. Uma ou duas linhas de introdução, só quando a revisão escreveu (`comentarios.<etapa>.introducao`).
2. Tabela Data | Evento / Ocorrência. Data sem hora; fato só programado leva "(programado)" na data, se o texto não disser. Uma frase objetiva por linha, sem nome de arquivo nem trecho de transcrição. Linha salmão = reprocesso; amarela = ocioso. Na etapa J, a tabela é Data | Interferência | Impacto; com `grupo` nos fatos, uma tabela por tipo, com subtítulo "J.1 — <tipo>" na ordem do primeiro fato (as sem tipo por último, em "Outras interferências"), e no fim a linha "Dias de equipe sem frente registrados no grupo" quando a revisão contou `dias_sem_frente`.
3. "Leitura da Etapa X:" em até três frases (`comentarios.<etapa>.leitura`); sem leitura revisada, o período da etapa em dias úteis.
4. "Status:" em uma linha (`comentarios.<etapa>.status`): o que está comprovado e o que não está. Sem status revisado, só a etapa que tem apenas fato programado ganha a linha ("programado, sem confirmação no grupo.").

Na etapa L, também a tabela Marco | Situação, a frase "Sem comprovação no grupo até <último registro>: …" com os marcos não concluídos (o termo assinado fica na tabela de pendências) e, se houver, Pendência em aberto | Status. Não existe etapa K.

## Análise de Prazos — Intervalos em Dias Úteis

Marco é o primeiro registro realizado de cada etapa (programação não conta; na etapa L, só a conclusão marcada). Os passos são só os marcos do ciclo, na ordem: chapas (A), medição (C), preliminar (D), aprovação (G), entrega (H), equipe (I) e conclusão (L); pedido de visita (B), revisões (E, F) e interferências (J) não entram, nem etapa com data anterior à do marco anterior. Em obra multifrente (fatos com `frente`), os intervalos são medidos dentro de cada frente, com o nome da frente na linha ("Banhos — …"), e a Nota Metodológica ganha a linha "Obra multifrente" com as frentes. Tabela Intervalo entre marcos | Dias úteis (mais a coluna Interpretação quando a revisão escreveu `interpretacao_intervalos`), em ordem de data, seguida de uma linha "pendente" (amarela) para cada frente que parou antes da conclusão, com a data que falta como dado não identificado (entrega, entrada da equipe ou conclusão), e a última linha "DURAÇÃO TOTAL DA OBRA" em amarelo: o período do grupo, o mesmo número do Quadro-Resumo e da Conclusão (sem período do grupo, "DURAÇÃO TOTAL REGISTRADA", do primeiro ao último registro). Intervalo acima de 20 dias úteis: linha amarela e número em vermelho, negrito. Quando há prazo contratual informado, tabela Prazo contratual de referência | Contrato | Realizado, com o realizado em vermelho quando passou do prazo. Figura 1: barras deitadas, uma por intervalo entre marcos. Figura 2: linha do tempo (Gantt) das etapas. As figuras são desenhadas na largura da página (16,2 cm) para a letra não encolher.

## Análise Técnica — Diagnóstico

Quando a revisão escreveu `diagnostico_temas`, abre com a tabela Tema | Avaliação | Leitura (Gargalo documentado, Ponto crítico, Comprovação incompleta, Fluxo eficiente, Não verificável; outra avaliação segura a versão final). Depois, cinco blocos numerados, cada um com tópicos curtos e datados: 1. Reprocessos identificados; 2. Tempos ociosos; 3. Atrasos operacionais internos; 4. Dependências externas; 5. Interferências de obra (Etapa J): impacto no cronograma e na produtividade. Sem revisão, cada bloco diz `dado não identificado (preencher na revisão)`.

## Conclusão Estratégica

Diagnóstico da eficiência do fluxo operacional; Principais pontos críticos de atraso (numerados); Impactos no prazo final; Recomendações práticas (tabela Prioridade | Medida proposta | Resultado esperado; só frases, numeradas); Pontos de controle recomendados (tópicos, quando a revisão escreveu `pontos_de_controle`). Termina com "— Fim do relatório —".

## Postura

O texto defende o registro da Armanilux com a evidência do grupo. Não acusa cliente, obra ou colega. Não transforma silêncio do grupo em culpa.
