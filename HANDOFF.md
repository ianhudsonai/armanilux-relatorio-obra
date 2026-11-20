# HANDOFF — armanilux-relatorio-obra (2026-11-20)

## Estado atual
Duas skills na `main` (PRs #5 a #44; 201 testes; CI verde no Ubuntu e no Windows com Python 3.10, 3.12 e 3.13): `preparar-projeto-armanilux` 1.3 e `relatorio-cronologico-obra` 1.13. As duas instaladas em `C:\Users\EuSou\.claude\skills\`, iguais à `main`.
Rodada de precisão (#44): aprovação revista não é marco, fato sem dia exato em faixa, "Quem segurou" no contrato, dias perdidos dos dois lados, rótulos corrigidos, gabarito (`tools/pontuar_relatorio.py`).
Avaliação de 2026-11-20 em `C:\Users\EuSou\Documents\Armanilux\avaliacao-v13-2026-11-19\` (fora do repo): `readiness.md` (pronto para enviar?), `baseline\` (relatório feito só com o prompt), `nota-v13-vs-prompt.md` (nota antes: 7,5/10; só prompt 6,5), `nota-v13-nova.md` (nota depois: 8,5/10, precisão 9,0), `gabarito-8977.1.json` (30 itens conferidos na conversa; NUNCA no repo), `nota-gabarito-v13-antes.txt` (10 de 30) e `-depois.txt` (30 de 30).
Obra de teste (FORA do repo) remontada em 2026-11-20: `v13` regravado, 133 de 133 fatos batem. O PDF não sai neste PC (sem Word nem LibreOffice); o `.docx` é a entrega. Cópia de antes: `D:\_ai-archive\2026-11-20\v13-antes-precisao\`.

## Decisões desta sessão
- Conclusão só com fato da etapa L marcado `"conclusao": true`; sem frente fecha a obra, com `frente` fecha só o ciclo da frente. Sem marca: "DADO NÃO IDENTIFICADO (pendente — ver Etapa L)", como no 8665.1 V3.
- Aprovação revista: aprovação seguida de revisão (E/F) e de nova aprovação da mesma frente não é marco; vale a que vem depois da última revisão seguida de aprovação. O Word diz "Aprovações revistas: ..."; a remontagem imprime `Aprovação revista:`. Para manter a primeira: `"marco": false` na nova. No Quadro de obra multifrente, "Primeira aprovação" continua a primeira da obra.
- Faixa: `data_evento` + `data_evento_ate` (fato entre duas datas) → Quadro "entre X e Y", intervalos e contrato "30–32 d.u.", barra tracejada; prazo com `inicio_ate`/`fim_ate`; faixa que passa do limite só no fim não é estouro ("talvez").
- Contrato: `quem_segurou` (coluna nova) e `"externo": true` (espera do outro lado: sem vermelho, fora da conta de atraso da Armanilux). Etapa J: `dias_perdidos_armanilux` somado ao lado de `dias_sem_frente`.
- `"programado": true` só para fato futuro programado/agendado. Ação feita que não é marco (cobrança, pedido, checklist enviado, "não realizada") leva `"marco": false`; a remontagem imprime `Aviso de programado:`. Liberação de frente não é entrada da equipe. Antes: `"programado": true` (programa, agenda) não vira marco, nem Quadro, nem contrato; a leitura do grupo já marca A, C, H, I e L por palavra. `"data_evento"` leva o marco ao dia do fato. Prazo com fim só programado: `"programado": true`; início sem data confirmada: tirar `fim` (sai "dado não identificado").
- `"frente"` nos fatos de obra multifrente: intervalos medidos dentro de cada frente; "Obra multifrente" na Nota Metodológica com 2+ frentes; `Aviso de frente` na remontagem para fato G/H/I/L sem frente, marco fora da ordem do ciclo e prazo com frente desconhecida.
- Cadeia de marcos só com A, C, D, G, H, I, L, na ordem do ciclo (maior sequência com datas em ordem). B, E, F e J nunca são passos.
- `"marco": false` = fato realizado fora do ciclo (reposição, entrega em andamento sem data de início): fica na tabela da etapa, não vira primeira entrega.
- Um total só: `duracao_da_obra` (período do grupo) no Quadro, na Análise de Prazos ("DURAÇÃO TOTAL DA OBRA") e na Conclusão. Linhas "pendente" (amarelas) mostram a data que falta em cada ciclo incompleto.
- Etapa J: `"grupo"` = tipo (uma tabela por tipo, J.1, J.2… na ordem do primeiro fato); `"dias_sem_frente"` contado pela revisão, cada data uma vez; total no fim da etapa J.
- Word e gráficos refazem marcos, contrato, duração e marcos de L dos eventos (remontar sem `--recalcular` não deixa número antigo).
- Na obra de teste: primeira entrega dos banhos entre 09/06 e 11/06/2026; living começou entre 05/08 e 11/08 (03/08 foi só a liberação); bancadas da cozinha entre 10/11 e 16/11; aprovações que valeram: banhos 24/04, living 03/06, cozinha 25/09; 4 dias sem frente da obra (21/08 saiu: a equipe moveu peças a pedido da obra) e 3 do lado da Armanilux (12/06, 28/07, 25/08; em 31/08 outra equipe foi); pisos 9 de 6 d.u. com espera da arquitetura (`externo`); valor do contrato não informado → lacuna.
- Antes já valiam: versão final fixa (`vN` regravado; `v2` só com conversa nova); conferência bloqueia a final; prazo contratual só com fonte escrita da época (`fonte_data`; posterior leva `*`); "dias" sem "úteis" = `dias_corridos`; coladas `[12:25, 03/07/2026] Nome:` viram mensagem; cores marrom `#442819` e dourado `#C3A56D`.

## Não mexer
- A ideia central e as etapas A–L (sem K) do `prompt.md`; só melhorias pequenas.
- Formato compacto do PDF aprovado (8665.1 V3) e os gráficos atuais (Ian gostou). A Figura 1 agora põe o nome da frente numa linha própria do rótulo; o estilo é o mesmo.
- Pergunta de áudio no preparo ("Quer que eu também entenda os áudios e vídeos… cerca de 484 MB…").
- Não apagar dados sensíveis do relatório. Imagem é só contexto, sem descrição no relatório.
- Repo é PÚBLICO: nunca commitar nome de cliente, zip, conversa ou relatório real (`tests/test_skill.py` barra alguns nomes).
- Instalar skills só no app em uso (Codex → `.codex\skills`; Claude Code → `.claude\skills`).

## Pendências (em ordem)
1. Teste no Codex deste PC (Ian tem o Codex instalado): instalar as skills pela linha de colagem do README, rodar a obra de teste numa pasta separada e pontuar com `tools/pontuar_relatorio.py --gabarito <gabarito> --obra-dir <pasta da obra do Codex>`. Mostra a precisão real que o Rogério terá (no PC dele quem revisa é o ChatGPT, não o Claude) e os cliques do app Codex.
2. Antes de enviar ao Rogério (`avaliacao-v13-2026-11-19\readiness.md`): README diz "três linhas" mas o bloco tem quatro (README.md:25, instalar.bat:5); confirmar no Codex deste PC qual app/pasta/permissão escolher e escrever os cliques no README; linha de socorro `.codex\skills` → `.agents\skills`. Depois, teste supervisionado no PC dele.
3. Sobras da nota nova (`nota-v13-nova.md`, só se valer): dias sem frente da obra talvez baixos (15–19/06); etapa C sem 09/04, 16/04 e 13/05 na tabela; living 13/05 → 22/05 = 7 de 6 d.u. fora do contrato; críticas da arquitetura à Armanilux (24/09, 28/10/2025, 08/07); lavanderia (pedra natural) cai na regra de 25 d.u.; aprovação do gourmet em 14/10 não é explícita; Quadro com as regras de prazo por extenso; recomendações em "evitar recorrência" e "otimizar próximas obras"; coluna "d.u. desde o evento anterior" nas tabelas das etapas.
4. Rodar `$preparar-projeto-armanilux` neste PC para trocar o venv 3.14 pelo 3.12 com as versões fixas (o antigo fica guardado).
5. Sobras (só se incomodarem): Quadro-Resumo sem linha de valor do contrato (está como lacuna); "Primeira entrega na obra" é da obra toda, não por frente; Gantt mostra todos os registros (inclusive reposição); "Cliente:" solto no grupo vale mais que o nome do arquivo; remontar não refaz folhas de contato.
6. Limpar textos automáticos antigos de `analyze.py` que o Word compacto não usa (`_comentarios_etapa`, `_conclusao`, `_gargalos`…).

## Como rodar
- Python: `C:\Users\EuSou\.armanilux-relatorio\venv\Scripts\python.exe` (config em `%USERPROFILE%\.armanilux-relatorio\config.json`).
- Testes: `python -m unittest discover -s tests` com `ARMANILUX_REGISTRO` apontando para um arquivo temporário (~1 min). Rodar um teste sozinho também com essa variável.
- Remontar a obra de teste: `run_pipeline.py --rebuild-only --recalcular --obra-dir "<pasta da obra>"`. Listar: `--listar`; gerar: `--indice 1`; concluir: `--concluir --indice 1`.
- Depois de mudar a skill: mover a cópia instalada para `D:\_ai-archive\<data>\` (anotar em `COMO-RESTAURAR.md`) e copiar a pasta do repo para `.claude\skills`.
- PRs: squash merge depois do CI verde (ver no `mcp__ccd_pr__get_status`). Depois de merge pelo `gh`, `git fetch` antes de comparar com `main`.
- Python inline em heredoc no Bash perde `\`: escreva o script em arquivo (Write) e rode.
- Disco C: está 95% cheio.

## Arquivos-chave
- `tools/pontuar_relatorio.py` — gabarito: confere `analise.json` + Word contra respostas certas (gabarito de obra real fora do repo).
- `skills/relatorio-cronologico-obra/scripts/analyze.py` — marcos (`conta_como_marco`, `faixas_dos_marcos`, `primeiros_marcos`, `_aprovacoes`/`aprovacoes_revistas`, `avisos_de_programado`, `marcos_em_ordem`, `intervalos_marcos_de`, `ciclos_incompletos`, `duracao_da_obra`, `avisos_de_frente`, `grupos_da_etapa_j`, `dias_sem_frente`).
- `skills/relatorio-cronologico-obra/scripts/build_docx.py` — Quadro-Resumo, Análise de Prazos, etapa J por tipo.
- `skills/relatorio-cronologico-obra/SKILL.md` (passo 4.2) e `references/analise-json.md` — campos da revisão: `conclusao`, `programado`, `data_evento`, `data_evento_ate`, `marco`, `frente`, `grupo`, `dias_sem_frente`, `dias_perdidos_armanilux`; no prazo: `inicio_ate`, `fim_ate`, `quem_segurou`, `externo`.
- `tests/test_conclusao.py`, `test_programado.py`, `test_frentes.py`, `test_duracao.py`, `test_etapa_j.py`, `test_fora_do_ciclo.py`, `test_rotulos.py`, `test_aprovacao_revista.py`, `test_faixa.py`, `test_dois_lados.py`, `test_pontuar.py` — uma correção por arquivo.
- `C:\Users\EuSou\Downloads\prompt.md` e o PDF 8665.1 V3 — referência do Rogério (fora do repo).

## Skills sugeridas
- `relatorio-cronologico-obra` — para remontar ou revisar a obra de teste.
- `mattpocock-skills:tdd` e `mattpocock-skills:code-review` — em qualquer correção nova.
