# analise.json

O arquivo fica em `04-transcricoes/analise.json`. O Word é montado a partir dele.

Campos que o script recalcula com `--recalcular`: `intervalos`, `intervalos_marcos`, `duracao_marcos` (período do grupo, o mesmo do Quadro-Resumo), `ciclos_incompletos` (frente que parou entre a aprovação e a conclusão), `confronto_contrato`, `lacunas`, `kpis`, `etapas`, `marcos` e, em cada evento, `destaque_auto` (cor sugerida).

Campos que vêm da leitura do zip, para o agente consultar. Não edite: `lacunas_automaticas`, `arquivos_fora_da_exportacao` (nomes dos arquivos que o WhatsApp não exportou), `documentos_texto`, `transcricoes`, `conversa` (caminho, dentro da obra, da conversa da última exportação lida; a conferência e a remontagem usam esta). `versao` (número da versão deste relatório, fixado na primeira gravação; uma conversa nova abre a seguinte).

Campos que a revisão preenche e o script preserva:

- `eventos_adicionais`: fatos que a leitura automática não achou. Cada item tem `data` (AAAA-MM-DD), `hora`, `etapa` (A a J ou L), `autor`, `ocorrencia` (uma frase, até 25 palavras), na etapa J `impacto`, e opcionalmente `destaque` (`reprocesso`, `ocioso` ou `nenhum`) e, só na etapa L, `"conclusao": true` no fato que registra o fim dos serviços e a validação final (sem ele, a conclusão sai como dado não identificado); `"programado": true` quando a mensagem só programa, agenda ou pede o fato (não vira marco); `data_evento` (AAAA-MM-DD) quando a mensagem conta um fato de outro dia (os marcos usam essa data); `frente` (nome do ambiente, sempre igual) em obra multifrente: os intervalos entre marcos são medidos dentro de cada frente. Repetidos são ignorados. A cada remontagem os fatos desta lista são refeitos: editar ou tirar um item muda o relatório, sem deixar a versão antiga
- `ajustes_eventos`: correções aplicadas também numa nova leitura do zip. Cada item escolhe o evento por `data`, `hora`, `autor`, `etapa_original` e traz `etapa`, `ocorrencia`, `impacto`, `destaque`, `conclusao`, `programado` (true ou false), `data_evento`, `frente`, ou `"remover": true`
- `prazos_contratuais`: prazos declarados no grupo ou em documento. Cada item tem `descricao`, `limite_du`, `fonte` e o período: `de` e `para` (etapas; com `frente`, só os fatos dessa frente) ou `inicio` e `fim` (datas). `fonte_data` (AAAA-MM-DD, quando a regra apareceu no grupo; obrigatório). `"unidade": "dias_corridos"` quando o prazo escrito é em dias, sem "úteis"; sem `unidade`, conta dias úteis. `"programado": true` quando o fim do período só foi programado: sem realizado
- `comentarios`: por letra de etapa, `introducao` (antes da tabela) e `leitura` (Leitura da Etapa)
- `diagnostico_prompt`: listas de tópicos em `reprocessos`, `tempos_ociosos`, `atrasos_internos`, `dependencias_externas`, `interferencias`
- `pontos_criticos`: lista de frases
- `impactos_prazo`: texto único
- `conclusao_personalizada`: texto único (diagnóstico da eficiência do fluxo)
- `recomendacoes_personalizadas`: lista de frases
- `lacunas_adicionais`: lista de frases curtas com o que faltou e não está em `lacunas_automaticas`
- `obra_ajustes`, `pendencias_revisadas`

`revisado` não é preservado: uma exportação nova da mesma obra traz mensagens novas, então o relatório volta a ser rascunho até a revisão gravar `"revisado": true` de novo. `"revisado": true` só vira versão final quando a conferência (`04-transcricoes/verificacao.md`) roda e não lista nenhum fato; senão sai rascunho.

`eventos` é a lista cronológica. `etapa` é uma letra de A, B, C, D, E, F, G, H, I, J ou L. `pendencias` usa `status` igual a `Pendente` só para item que o grupo deixou aberto.

Datas internas estão em `AAAA-MM-DD`. O Word mostra `DD/MM/AAAA`. Não edite o número de dias úteis à mão: rode `--recalcular`.

Não grave este JSON de obra real no repositório público.
