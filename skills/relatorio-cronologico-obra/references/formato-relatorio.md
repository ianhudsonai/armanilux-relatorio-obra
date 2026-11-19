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

Marco é o primeiro registro de cada etapa, como na tabela do relatório aprovado (8665.1 V3). Tabela Intervalo entre marcos | Dias úteis: uma linha por par de marcos em ordem de data, com o nome da etapa e a data entre parênteses, e a última linha "Duração total registrada". Sem cor de semáforo: intervalo de calendário não é veredito. Figura 1: barras deitadas, uma por intervalo entre marcos. Figura 2: linha do tempo (Gantt) das etapas, do primeiro ao último registro. As figuras são desenhadas na largura da página (16,2 cm) para a letra não encolher.

Os intervalos entre todas as datas com registro continuam no `analise.json` (`intervalos`) e servem aos textos das etapas e dos gargalos.

## 5. Diagnóstico

Gargalos numerados e tabela Natureza | Diagnóstico.

## 6. Recomendações

Lista numerada.

## 7. Conclusão

Diagnóstico do fluxo, ponto crítico, impacto e uma recomendação final. Em seguida:

- Registro fotográfico: só as fotos e quadros de vídeo que a revisão descreveu, em ordem de data, com legenda "data · Etapa X — o que a imagem mostra (arquivo)". Sem tabela de nomes de arquivo.
- Lacunas de contexto: o que não pôde ser lido ou confirmado (arquivos fora da exportação, documentos sem texto, áudios sem transcrição e o que a revisão anotou).
- Nota de rastreabilidade.

## Postura

O texto defende o registro da Armanilux com a evidência do grupo. Não acusa cliente, obra ou colega. Não transforma silêncio do grupo em culpa.
