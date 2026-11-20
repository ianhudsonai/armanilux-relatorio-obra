# HANDOFF — armanilux-relatorio-obra (2026-11-19)

## Estado atual
Duas skills na `main` (PRs #5 a #42; 177 testes; CI verde no Ubuntu e no Windows com Python 3.10, 3.12 e 3.13): `preparar-projeto-armanilux` 1.3 e `relatorio-cronologico-obra` 1.12. As duas instaladas em `C:\Users\EuSou\.claude\skills\`, iguais à `main`.
As 5 lacunas de qualidade do v13 (avaliação em `C:\Users\EuSou\Documents\Armanilux\avaliacao-2026-11-19\`) foram corrigidas em #36–#40, mais dois achados da remontagem em #41–#42.
Obra de teste (pasta em `Documents\Armanilux\Relatorios-de-Obra\`, FORA do repo) remontada em 2026-11-19 com as marcas novas: `v13` regravado (124 de 124 fatos batem; sem aviso de frente; os 3 avisos de prazo com fonte posterior continuam, com *). O PDF não sai neste PC (sem Word nem LibreOffice); o `.docx` é a entrega. Cópia de antes: `D:\_ai-archive\2026-11-19\v13-antes-correcoes-de-qualidade\`.

## Decisões desta sessão
- Conclusão só com fato da etapa L marcado `"conclusao": true`; sem frente fecha a obra, com `frente` fecha só o ciclo da frente. Sem marca: "DADO NÃO IDENTIFICADO (pendente — ver Etapa L)", como no 8665.1 V3.
- `"programado": true` (programa, agenda, pede, cobra, "não realizada") não vira marco, nem Quadro, nem contrato; a leitura do grupo já marca A, C, H, I e L por palavra. `"data_evento"` leva o marco ao dia do fato. Prazo com fim só programado: `"programado": true`; início sem data confirmada: tirar `fim` (sai "dado não identificado").
- `"frente"` nos fatos de obra multifrente: intervalos medidos dentro de cada frente; "Obra multifrente" na Nota Metodológica com 2+ frentes; `Aviso de frente` na remontagem para fato G/H/I/L sem frente, marco fora da ordem do ciclo e prazo com frente desconhecida.
- Cadeia de marcos só com A, C, D, G, H, I, L, na ordem do ciclo (maior sequência com datas em ordem). B, E, F e J nunca são passos.
- `"marco": false` = fato realizado fora do ciclo (reposição, entrega em andamento sem data de início): fica na tabela da etapa, não vira primeira entrega.
- Um total só: `duracao_da_obra` (período do grupo) no Quadro, na Análise de Prazos ("DURAÇÃO TOTAL DA OBRA") e na Conclusão. Linhas "pendente" (amarelas) mostram a data que falta em cada ciclo incompleto.
- Etapa J: `"grupo"` = tipo (uma tabela por tipo, J.1, J.2… na ordem do primeiro fato); `"dias_sem_frente"` contado pela revisão, cada data uma vez; total no fim da etapa J.
- Word e gráficos refazem marcos, contrato, duração e marcos de L dos eventos (remontar sem `--recalcular` não deixa número antigo).
- Na obra de teste: primeira entrega dos banhos = 11/06/2026 (a mensagem das 17:17 cita "a última entrega"; a de 09/06 era programada); bancadas da cozinha sem data de início (programada 10/11; "estão sendo entregues" em 16/11, colada); 5 dias de equipe sem frente (15/06, 03 e 04/08, 21/08, 16/09); valor do contrato não informado (só a divisão do sinal) → lacuna.
- Antes já valiam: versão final fixa (`vN` regravado; `v2` só com conversa nova); conferência bloqueia a final; prazo contratual só com fonte escrita da época (`fonte_data`; posterior leva `*`); "dias" sem "úteis" = `dias_corridos`; coladas `[12:25, 03/07/2026] Nome:` viram mensagem; cores marrom `#442819` e dourado `#C3A56D`.

## Não mexer
- A ideia central e as etapas A–L (sem K) do `prompt.md`; só melhorias pequenas.
- Formato compacto do PDF aprovado (8665.1 V3) e os gráficos atuais (Ian gostou). A Figura 1 agora põe o nome da frente numa linha própria do rótulo; o estilo é o mesmo.
- Pergunta de áudio no preparo ("Quer que eu também entenda os áudios e vídeos… cerca de 484 MB…").
- Não apagar dados sensíveis do relatório. Imagem é só contexto, sem descrição no relatório.
- Repo é PÚBLICO: nunca commitar nome de cliente, zip, conversa ou relatório real (`tests/test_skill.py` barra alguns nomes).
- Instalar skills só no app em uso (Codex → `.codex\skills`; Claude Code → `.claude\skills`).

## Pendências (em ordem)
1. Ian abrir o `v13` (`05-relatorios\Relatorio-Cronologico-Obra-8977.1-v13.docx`, na pasta da obra de teste) e comparar com o PDF aprovado. A remontagem não relê a conversa: as 77 coladas só entram numa exportação nova.
2. Teste real no PC do Rogério (passos em `avaliacao-2026-11-19\3-pronto-para-enviar.md`, "What Rogério must do himself"): único jeito de provar a instalação no Codex sem Python.
3. Rodar `$preparar-projeto-armanilux` neste PC para trocar o venv 3.14 pelo 3.12 com as versões fixas (o antigo fica guardado).
4. Sobras (só se incomodarem): Quadro-Resumo sem linha de valor do contrato (está como lacuna); "Primeira entrega na obra" é da obra toda, não por frente; Gantt mostra todos os registros (inclusive reposição); "Cliente:" solto no grupo vale mais que o nome do arquivo; remontar não refaz folhas de contato.
5. Limpar textos automáticos antigos de `analyze.py` que o Word compacto não usa (`_comentarios_etapa`, `_conclusao`, `_gargalos`…).

## Como rodar
- Python: `C:\Users\EuSou\.armanilux-relatorio\venv\Scripts\python.exe` (config em `%USERPROFILE%\.armanilux-relatorio\config.json`).
- Testes: `python -m unittest discover -s tests` com `ARMANILUX_REGISTRO` apontando para um arquivo temporário (~1 min). Rodar um teste sozinho também com essa variável.
- Remontar a obra de teste: `run_pipeline.py --rebuild-only --recalcular --obra-dir "<pasta da obra>"`. Listar: `--listar`; gerar: `--indice 1`; concluir: `--concluir --indice 1`.
- Depois de mudar a skill: mover a cópia instalada para `D:\_ai-archive\<data>\` (anotar em `COMO-RESTAURAR.md`) e copiar a pasta do repo para `.claude\skills`.
- PRs: squash merge depois do CI verde (ver no `mcp__ccd_pr__get_status`). Depois de merge pelo `gh`, `git fetch` antes de comparar com `main`.
- Python inline em heredoc no Bash perde `\`: escreva o script em arquivo (Write) e rode.
- Disco C: está 95% cheio.

## Arquivos-chave
- `skills/relatorio-cronologico-obra/scripts/analyze.py` — marcos (`conta_como_marco`, `primeiros_marcos`, `marcos_em_ordem`, `intervalos_marcos_de`, `ciclos_incompletos`, `duracao_da_obra`, `avisos_de_frente`, `grupos_da_etapa_j`, `dias_sem_frente`).
- `skills/relatorio-cronologico-obra/scripts/build_docx.py` — Quadro-Resumo, Análise de Prazos, etapa J por tipo.
- `skills/relatorio-cronologico-obra/SKILL.md` (passo 4.2) e `references/analise-json.md` — campos da revisão: `conclusao`, `programado`, `data_evento`, `marco`, `frente`, `grupo`, `dias_sem_frente`.
- `tests/test_conclusao.py`, `test_programado.py`, `test_frentes.py`, `test_duracao.py`, `test_etapa_j.py`, `test_fora_do_ciclo.py` — uma correção por arquivo.
- `C:\Users\EuSou\Downloads\prompt.md` e o PDF 8665.1 V3 — referência do Rogério (fora do repo).

## Skills sugeridas
- `relatorio-cronologico-obra` — para remontar ou revisar a obra de teste.
- `mattpocock-skills:tdd` e `mattpocock-skills:code-review` — em qualquer correção nova.
