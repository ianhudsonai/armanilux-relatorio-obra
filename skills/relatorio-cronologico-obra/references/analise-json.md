# analise.json

O arquivo fica em `04-transcricoes/analise.json`. O Word é montado a partir dele.

Na etapa G, o marco de cada frente é a aprovação que valeu: aprovação seguida de revisão (E ou F) e de nova aprovação da mesma frente é revista. Para manter a primeira, marque a nova com `"marco": false`.

Campos que o script recalcula com `--recalcular`: `intervalos`, `intervalos_marcos`, `duracao_marcos` (período do grupo, o mesmo do Quadro-Resumo), `ciclos_incompletos` (frente que parou entre a aprovação e a conclusão), `confronto_contrato`, `lacunas`, `kpis`, `etapas`, `marcos` e, em cada evento, `destaque_auto` (cor sugerida).

Campos que vêm da leitura do zip, para o agente consultar. Não edite: `lacunas_automaticas`, `arquivos_fora_da_exportacao` (nomes dos arquivos que o WhatsApp não exportou), `documentos_texto`, `transcricoes`, `conversa` (caminho, dentro da obra, da conversa da última exportação lida; a conferência e a remontagem usam esta). `versao` (número da versão deste relatório, fixado na primeira gravação; uma conversa nova abre a seguinte).

Campos que a revisão preenche e o script preserva:

- `eventos_adicionais`: fatos que a leitura automática não achou. Cada item tem `data` (AAAA-MM-DD), `hora`, `etapa` (A a J ou L), `autor`, `ocorrencia` (uma frase, até 25 palavras), na etapa J `impacto`, e opcionalmente `destaque` (`reprocesso`, `ocioso` ou `nenhum`) e, só na etapa L, `"conclusao": true` no fato que registra o fim dos serviços e a validação final (sem ele, a conclusão sai como dado não identificado); `"programado": true` quando a mensagem só programa, agenda ou pede o fato (não vira marco); `"marco": false` em fato realizado que não é marco do ciclo (reposição, peça extra); `data_evento` (AAAA-MM-DD) quando a mensagem conta um fato de outro dia (os marcos usam essa data); `data_evento_ate` (AAAA-MM-DD) quando o grupo só mostra que o fato aconteceu entre `data_evento` e esta data (o Word mostra a faixa e conta os dias úteis em faixa); na etapa J, `grupo` (tipo da interferência: o Word faz uma tabela por tipo, J.1, J.2…) `dias_sem_frente` (dias de equipe na obra sem poder trabalhar por causa da obra, só quando o grupo permite contar; o Word soma) e `dias_perdidos_armanilux` (dias perdidos por causa da Armanilux: imprevisto, equipe, veículo; o Word soma ao lado); `frente` (nome do ambiente, sempre igual) em obra multifrente: os intervalos entre marcos são medidos dentro de cada frente. Repetidos são ignorados. A cada remontagem os fatos desta lista são refeitos: editar ou tirar um item muda o relatório, sem deixar a versão antiga
- `ajustes_eventos`: correções aplicadas também numa nova leitura do zip. Cada item escolhe o evento por `data`, `hora`, `autor`, `etapa_original` e traz `etapa`, `ocorrencia`, `impacto`, `destaque`, `conclusao`, `programado` (true ou false), `marco` (false para tirar do ciclo), `data_evento`, `data_evento_ate`, `frente`, `grupo`, `dias_sem_frente`, `dias_perdidos_armanilux`, ou `"remover": true`
- `prazos_contratuais`: prazos declarados no grupo ou em documento. Cada item tem `descricao`, `limite_du`, `fonte` e o período: `de` e `para` (etapas; com `frente`, só os fatos dessa frente) ou `inicio` e `fim` (datas). `fonte_data` (AAAA-MM-DD, quando a regra apareceu no grupo; obrigatório). `"unidade": "dias_corridos"` quando o prazo escrito é em dias, sem "úteis"; sem `unidade`, conta dias úteis. `"programado": true` quando o fim do período só foi programado: sem realizado. `inicio_ate` e `fim_ate` quando o grupo só dá uma faixa para a data (realizado em faixa). `quem_segurou` (frase curta: quem o período esperava, com data) e `"externo": true` quando a espera era do outro lado (o prazo não conta como atraso da Armanilux)
- `comentarios`: por letra de etapa, `introducao` (antes da tabela), `leitura` (Leitura da Etapa) e `status` (veredito em uma linha)
- `interpretacao_intervalos`: lista de `{"de", "para", "frente" (opcional), "texto"}`; com algum item, a tabela de intervalos ganha a coluna "Interpretação"
- `diagnostico_temas`: lista de `{"tema", "avaliacao", "leitura"}`; `avaliacao` é "Gargalo documentado", "Ponto crítico", "Comprovação incompleta", "Fluxo eficiente" ou "Não verificável"
- `pontos_de_controle`: lista de frases (liberação para medição, projeto, produção, entrega, instalação, encerramento)
- `diagnostico_prompt`: listas de tópicos em `reprocessos`, `tempos_ociosos`, `atrasos_internos`, `dependencias_externas`, `interferencias`
- `pontos_criticos`: lista de frases
- `impactos_prazo`: texto único
- `conclusao_personalizada`: texto único (diagnóstico da eficiência do fluxo)
- `recomendacoes_personalizadas`: lista de `{"prioridade", "medida", "resultado"}` (vira tabela) ou de frases (lista numerada)
- `lacunas_adicionais`: lista de frases curtas com o que faltou e não está em `lacunas_automaticas`
- `obra_ajustes`, `pendencias_revisadas`

`revisado` não é preservado: uma exportação nova da mesma obra traz mensagens novas, então o relatório volta a ser rascunho até a revisão gravar `"revisado": true` de novo. `"revisado": true` só vira versão final quando a conferência (`04-transcricoes/verificacao.md`) roda e não lista nenhum fato, toda parte de `04-transcricoes/revisao-progresso.md` e todo item de `04-transcricoes/conferencia.md` estão com `[x]`, e `conferencia_independente` está gravado; senão sai rascunho.

`conferencia_independente`: como a conferência de conteúdo (revisão 4.4) foi feita, `{"como": "subagente", "data": "AAAA-MM-DD"}` ou `{"como": "segunda passada", "data": "AAAA-MM-DD"}`. Também não é preservado numa exportação nova: confira de novo. As marcas `[x]` das duas listas continuam onde a parte ou o item não mudou.

`eventos` é a lista cronológica. `etapa` é uma letra de A, B, C, D, E, F, G, H, I, J ou L. `pendencias` usa `status` igual a `Pendente` só para item que o grupo deixou aberto.

Datas internas estão em `AAAA-MM-DD`. O Word mostra `DD/MM/AAAA`. Não edite o número de dias úteis à mão: rode `--recalcular`.

Não grave este JSON de obra real no repositório público.
