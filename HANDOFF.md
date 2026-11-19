# HANDOFF — armanilux-relatorio-obra (2026-11-19)

## Estado atual
Duas skills na `main` (PRs #5 a #19; 97 testes; CI verde no Ubuntu e no Windows): `preparar-projeto-armanilux` (perguntas + instalação) e `relatorio-cronologico-obra` (zip do WhatsApp → Word). A skill instalada em `C:\Users\EuSou\.claude\skills\relatorio-cronologico-obra` é a 1.8, igual à `main`.
Relatório no formato compacto do PDF aprovado (8665.1 V3): Nota Metodológica, Quadro-Resumo, etapas A–L com cores (salmão = reprocesso, amarelo = ocioso), Análise de Prazos (vermelho = intervalo longo ou prazo estourado), confronto com prazos contratuais, Diagnóstico em 5 blocos, Conclusão.
Obra de teste (pasta em `Documents\Armanilux\Relatorios-de-Obra\`, FORA do repo): v12 revisado, 122 fatos conferidos com o grupo. Backup da análise antes das mudanças de hoje: `04-transcricoes/analise.antes-v12.json`. Versões descartadas do v12 estão em `D:\_ai-archive\2026-11-19\`.

## Decisões desta sessão
- Rascunho sai como `-vN-rascunho.docx` e é regravado a cada remontagem; `vN` só nasce com `"revisado": true` — não gastar versão em revisão.
- Fatos de `eventos_adicionais` são refeitos a cada remontagem (marca `"origem": "revisao"`) — editar não duplica.
- Prazo contratual: usar quando o grupo ou um documento declara, nunca deduzir. Vale a regra já escrita quando o período começou (`fonte_data`); em conflito, a fonte da época decide número e unidade. Fonte posterior ao início leva `*` no Word e "Aviso de prazo" na remontagem — erro real do v12 (orçamento de 17/06/2026 usado para instalação de 09–15/06).
- Prazo escrito só em "dias" usa `"unidade": "dias_corridos"`; sem isso, dias úteis.
- Na obra de teste, os 3 prazos de 6 d.u. ficam com `*` (só aparecem no orçamento de 17/06/2026, como regra geral); instalação é 5 d.u. pela mensagem de 02/06/2026 (cumprido, 4 d.u.).
- A skill entrega o Word na conversa (`RELATORIO_WORD:`; `--mostrar` abre a pasta).
- Seguir o `prompt.md` do Rogério; só melhorias pequenas. Não apagar dados sensíveis do relatório. Relatório curto: o contexto inteiro é para o agente, não para o Word. Imagem é só contexto, sem descrição no relatório.
- Cores: marrom `#442819` e dourado `#C3A56D`. `8977.1.v10`: `.vNN` é versão, a obra é `8977.1`.
- Instalar skills só no app em uso (Codex → `.codex\skills`; Claude Code → `.claude\skills`).
- Datas de mensagens coladas: conferido no v12 (25 coladas). Nenhum fato usa a data da colagem no lugar da original; não precisou reprocessar. Dois pontos para o Ian decidir: a autorização do Arqto. Sérgio para medir com a banheira só apoiada foi em 03/11 19:04 (colada), o fato está em 04/11 11:11 (aviso no grupo); o pedido do Sérgio em 21/08 para desocupar cozinha e copa dos materiais da Armani (colado em 28/09) não virou fato.
- Transcrição com cache: `04-transcricoes/transcricoes-cache.json` guarda SHA-256, modelo e texto de cada áudio/vídeo. Arquivo igual não volta ao Whisper; execução interrompida continua; `--skip-transcribe` mantém o que já existe. `.txt` de antes do cache só vale na primeira execução (sem cache). Na obra de teste, as 61 transcrições entraram no cache sem refazer.

## Não mexer
- A ideia central e as etapas A–L (sem K) do `prompt.md`.
- Formato compacto do PDF aprovado (8665.1 V3) e os gráficos atuais (Ian gostou).
- Pergunta de áudio no preparo ("Quer que eu também entenda os áudios e vídeos… cerca de 484 MB…").
- Repo é PÚBLICO: nunca commitar nome de cliente, zip, conversa ou relatório real (`tests/test_skill.py` barra alguns nomes).

## Pendências (em ordem)
1. Ian abrir o v12 da obra de teste e comparar com o PDF aprovado (8665.1 V3).
2. Ian decidir os dois pontos das mensagens coladas (ver Decisões).
3. Instalação: linha de colagem citando `$skill-installer` e as URLs `/tree/main/skills/<nome>` (README, AGENTS.md).
4. Limpar textos automáticos antigos de `analyze.py` (`_impacto`, `_produtividade`, `_comentarios_etapa`, gargalos, responsabilidades) que o Word compacto não usa.

## Como rodar
- Python: `C:\Users\EuSou\.armanilux-relatorio\venv\Scripts\python.exe` (config em `%USERPROFILE%\.armanilux-relatorio\config.json`).
- Testes: `python -m unittest discover -s tests` com `ARMANILUX_REGISTRO` apontando para um arquivo temporário.
- `run_pipeline.py --listar`; gerar: `--indice 1` ou `--todas`; remontar após revisão: `--rebuild-only --recalcular --obra-dir "<pasta da obra>"`; concluir: `--concluir --indice 1`.
- Depois de mudar a skill: mover a cópia instalada para `D:\_ai-archive\<data>\` (anotar em `COMO-RESTAURAR.md`) e copiar a pasta do repo para `.claude\skills`.
- PRs: squash merge depois do CI verde (`gh pr checks <n> --watch` em segundo plano).
- Python inline em heredoc no Bash perde `\\`: escreva script em arquivo (Write) e rode.

## Arquivos-chave
- `skills/relatorio-cronologico-obra/SKILL.md` — fluxo e revisão obrigatória do agente (regras de prazo no passo 4.2, item 5).
- `skills/relatorio-cronologico-obra/scripts/run_pipeline.py` — entrada de tudo; avisos de prazo e nome do arquivo.
- `skills/relatorio-cronologico-obra/scripts/analyze.py` — etapas, intervalos, `confronto_contrato`, `_juntar_adicionais`.
- `skills/relatorio-cronologico-obra/scripts/build_docx.py` — formato do Word, `proxima_versao`.
- `C:\Users\EuSou\Downloads\prompt.md` e o PDF 8665.1 V3 — referência do Rogério (fora do repo).

## Skills sugeridas
- `mattpocock-skills:tdd` — cada pendência com teste antes.
- `mattpocock-skills:code-review` — antes de abrir cada PR.
- `relatorio-cronologico-obra` — para testar de ponta a ponta na obra real.
