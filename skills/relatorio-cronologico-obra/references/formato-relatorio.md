# Formato do relatório

Português do Brasil, formal, técnico, neutro, sem emoji. Modelo: o relatório aprovado da obra 8665.1 V3 — curto, uma tabela de fatos por etapa, cores de destaque, análise de prazos, diagnóstico em tópicos e conclusão. O script `build_docx.py` já monta esta ordem. O relatório não é o lugar do contexto inteiro: o agente lê tudo para escrever pouco e certo.

## Capa

Título, obra e cliente, fornecedor, construtora, arquitetura, endereço, período, base documental, data de emissão e quem elaborou. Campo vazio vira `dado não identificado`.

## Nota Metodológica

Um parágrafo sobre a fonte (grupo, documentos, transcrições locais) e a regra do `dado não identificado`. Depois, em linhas com rótulo:

- Limites do material: as lacunas, em frases curtas (arquivos que não vieram na exportação, documentos sem texto, áudios sem transcrição, o que a revisão anotou).
- Dias úteis: a convenção de contagem.
- Prazos contratuais de referência: só quando o grupo ou um documento informa, com a fonte.
- Convenção de cores: salmão = reprocesso ou retrabalho; amarelo = tempo ocioso, espera ou pendência; vermelho na Análise de Prazos = passou do prazo contratual informado ou, sem prazo informado, intervalo entre marcos acima de 20 dias úteis.

## Quadro-Resumo da Obra

Tabela Indicador | Valor: início do grupo, primeiros marcos (chapas, medição, aprovação, entrega, instalação), último registro, duração em dias corridos e úteis, conclusão, prazo contratual.

## Etapas A a L

Cada etapa:

1. Uma ou duas linhas de introdução, só quando a revisão escreveu (`comentarios.<etapa>.introducao`).
2. Tabela Data | Evento / Ocorrência. Data sem hora. Uma frase objetiva por linha, sem nome de arquivo nem trecho de transcrição. Linha salmão = reprocesso; amarela = ocioso. Na etapa J, a tabela é Data | Interferência | Impacto.
3. "Leitura da Etapa X:" em até três frases (`comentarios.<etapa>.leitura`); sem leitura revisada, o período da etapa em dias úteis.

Na etapa L, também a tabela Marco | Situação e, se houver, Pendência em aberto | Status. Não existe etapa K.

## Análise de Prazos — Intervalos em Dias Úteis

Marco é o primeiro registro de cada etapa. Tabela Intervalo entre marcos | Dias úteis, em ordem de data, com a última linha "DURAÇÃO TOTAL REGISTRADA" em amarelo. Intervalo acima de 20 dias úteis: linha amarela e número em vermelho, negrito. Quando há prazo contratual informado, tabela Prazo contratual de referência | Contrato | Realizado, com o realizado em vermelho quando passou do prazo. Figura 1: barras deitadas, uma por intervalo entre marcos. Figura 2: linha do tempo (Gantt) das etapas. As figuras são desenhadas na largura da página (16,2 cm) para a letra não encolher.

## Análise Técnica — Diagnóstico

Cinco blocos numerados, cada um com tópicos curtos e datados: 1. Reprocessos identificados; 2. Tempos ociosos; 3. Atrasos operacionais internos; 4. Dependências externas; 5. Interferências de obra (Etapa J): impacto no cronograma e na produtividade. Sem revisão, cada bloco diz `dado não identificado (preencher na revisão)`.

## Conclusão Estratégica

Diagnóstico da eficiência do fluxo operacional; Principais pontos críticos de atraso (numerados); Impactos no prazo final; Recomendações práticas (numeradas). Termina com "— Fim do relatório —".

## Postura

O texto defende o registro da Armanilux com a evidência do grupo. Não acusa cliente, obra ou colega. Não transforma silêncio do grupo em culpa.
