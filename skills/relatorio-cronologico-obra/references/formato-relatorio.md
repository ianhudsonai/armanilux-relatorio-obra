# Formato do relatório

Português do Brasil, formal, técnico, neutro, sem emoji. O script `build_docx.py` já monta esta ordem. Ao corrigir texto, manter a ordem e os rótulos.

## Cabeçalho

Obra, cliente, construtora, engenheiro, arquitetura, responsável Armanilux, endereço, período, fonte, prazo contratual. Campo vazio vira `dado não identificado`.

## 1. Objetivo e critérios

Nomear as três categorias: Atividade realizada, Pendência identificada, Dado não identificado. Reproduzir a regra de dias úteis e a leitura das cores (até 2 fluxo contínuo, 3 a 5 atenção, 6 ou mais intervalo longo).

## 2. Resumo executivo

Quatro cartões, número grande e legenda:

1. Dias úteis no período
2. Revisões de projeto
3. Interferências registradas
4. Maior intervalo sem registro (dias úteis)

O quarto cartão não se chama atraso.

## 3. Etapas A a L

Tabela Data | Ocorrência. Na etapa J, a tabela é Data | Interferência | Impacto.

Em seguida, rótulos em negrito:

- Intervalos relevantes
- Situação
- Ponto crítico
- Gargalo
- Avaliação
- Conclusão da etapa

Na etapa J, ainda:

- J.1 pendências por item, com status Pendente quando o item segue aberto
- J.2 impacto na produtividade

Na etapa L, além da tabela Data | Ocorrência, incluir a tabela Marco | Situação (Concluído, Pendente ou dado não identificado). O script não cria uma etapa K no meio.

Evidência de arquivo na ocorrência: `Mídia: nome-do-arquivo` para foto, áudio e vídeo; `Documento: nome` para PDF e Word.

## 4. Dias úteis entre marcos

Tabela De | Até | Marcos | Dias úteis | Leitura, com a célula de leitura colorida. Figura 1: gráfico de barras colorido. Figura 2: linha do tempo (Gantt) das etapas, com borda vermelha quando a etapa vem depois de um intervalo longo.

## 5. Diagnóstico

Gargalos numerados e tabela Natureza | Diagnóstico.

## 6. Recomendações

Lista numerada.

## 7. Conclusão

Diagnóstico do fluxo, ponto crítico, impacto e uma recomendação final. Em seguida, o anexo de mídias (uma linha por arquivo relevante, mais as imagens que couberem) e a nota de rastreabilidade.

## Postura

O texto defende o registro da Armanilux com a evidência do grupo. Não acusa cliente, obra ou colega. Não transforma silêncio do grupo em culpa.
