# HANDOFF — armanilux-relatorio-obra (2026-11-19)

## Estado atual
Duas skills na `main` (PRs #5 a #27; 115 testes; CI verde no Ubuntu e no Windows): `preparar-projeto-armanilux` 1.2 e `relatorio-cronologico-obra` 1.10. As duas instaladas em `C:\Users\EuSou\.claude\skills\`, iguais à `main`.
Os 6 bloqueadores da avaliação (`C:\Users\EuSou\Documents\Armanilux\avaliacao-2026-11-19\0-resumo.md`) foram corrigidos com teste antes, em 4 PRs: #24 (nova exportação), #25 (coladas), #26 (versões), #27 (instalação).
Obra de teste (pasta em `Documents\Armanilux\Relatorios-de-Obra\`, FORA do repo): v12 revisado, 123 fatos conferidos. Ainda não remontada com o código novo.

## Decisões desta sessão
- Nova exportação de obra já revisada volta a ser rascunho (`revisado` não é preservado); `eventos_adicionais`, ajustes e textos da revisão continuam. O script avisa para conferir as mensagens novas e a conclusão.
- `analise.json` guarda `conversa` (o `.txt` da última exportação lida). Sem essa marca (análise antiga), vale o `.txt` mais recente, não o maior.
- `analise.json` guarda `versao`. A final `vN` tem o número do rascunho e é regravada a cada remontagem (corrigir erro não gasta versão). `v2` só com conversa nova. Rascunhos da versão final vão para `05-relatorios/rascunhos/` (nada é apagado; nome repetido ganha `-2`). Final aberta no Word: o script pede para fechar e remontar.
- Obra antiga com `revisado: true` e sem `versao` (a obra de teste) ganha uma versão a mais uma única vez (v13) na primeira remontagem; depois fica fixa.
- Coladas no formato `[12:25, 03/07/2026] Nome:` agora viram mensagem com autor e hora originais. Na obra de teste: coladas reconhecidas 25 → 77, em 13 datas (antes 5). Segundos/AM-PM dentro do colchete colado e data mês/dia não são tratados (não aparecem nas conversas reais).
- Linha de colagem: se o `$skill-installer` não rodar (PC sem Python), baixar o zip com PowerShell e copiar as duas pastas; os comandos estão no AGENTS.md (TLS 1.2, sem trocar pasta que já existe). O instalador do preparo é achado pela pasta da própria skill (`run_pipeline.instalador_do_preparo()`; SKILL.md usa `<pasta-de-skills>`).
- `test_entrega` passa a usar registro temporário. Um teste rodado sozinho tinha gravado a obra fictícia 1001 no registro real; a entrada foi tirada (cópia em `D:\_ai-archive\2026-11-19\registro-antes-de-tirar-obra-1001-de-teste.json`).
- Antes já valiam: transcrição com cache por arquivo; entrega Word, PDF ou link escolhida no preparo; prazo contratual só com fonte escrita da época (`fonte_data`; posterior leva `*`); "dias" sem "úteis" = `dias_corridos`; cores marrom `#442819` e dourado `#C3A56D`.

## Não mexer
- A ideia central e as etapas A–L (sem K) do `prompt.md`; só melhorias pequenas.
- Formato compacto do PDF aprovado (8665.1 V3) e os gráficos atuais (Ian gostou).
- Pergunta de áudio no preparo ("Quer que eu também entenda os áudios e vídeos… cerca de 484 MB…").
- Não apagar dados sensíveis do relatório. Imagem é só contexto, sem descrição no relatório.
- Repo é PÚBLICO: nunca commitar nome de cliente, zip, conversa ou relatório real (`tests/test_skill.py` barra alguns nomes).
- Instalar skills só no app em uso (Codex → `.codex\skills`; Claude Code → `.claude\skills`).

## Pendências (em ordem)
1. Remontar a obra de teste de verdade com o código novo (`--rebuild-only --recalcular`). Ensaio feito numa cópia (mídias trocadas por arquivos vazios de mesmo nome): 123 de 123 fatos batem, sai `v13` uma vez e a segunda remontagem regrava o mesmo `v13`. A remontagem não relê a conversa; as 77 coladas só entram numa exportação nova. Na pasta real, só remontar se o Ian quiser o `v13` ao lado do `v12`.
2. "Deveria corrigir" do `0-resumo.md`: verificação pendente bloqueando versão final, confirmar obra/cliente com sim/não, respeitar "não" do áudio, travar versão do Python (3.10–3.13) e das bibliotecas, texto de privacidade honesto, aviso de exportação cortada, datas das fotos pela mensagem, aviso "pode levar alguns minutos" ao carregar o modelo, tempo limite de comandos longos.
3. Pequenos que sobraram das revisões: remontagem não atualiza o registro local (`registro.registrar_relatorio` só na exportação nova); SKILL.md 4.1 fala de "(encaminhada no grupo por …)", marca que só existe no `analise.json`, não no `.txt`.
4. Lacunas de qualidade do v12 (conclusão em 14/09 errada, intervalos misturando frentes, "programado" contado como feito, datas finais e total 304/302, etapa J por tipo).
5. Ian abrir o v12 e comparar com o PDF aprovado. Depois, teste real no PC do Rogério (passos em `3-pronto-para-enviar.md`, "What Rogério must do himself"): é o único jeito de provar a instalação no Codex sem Python e a pasta de skills que o Codex usa.
6. Limpar textos automáticos antigos de `analyze.py` que o Word compacto não usa.

## Como rodar
- Python: `C:\Users\EuSou\.armanilux-relatorio\venv\Scripts\python.exe` (config em `%USERPROFILE%\.armanilux-relatorio\config.json`).
- Testes: `python -m unittest discover -s tests` com `ARMANILUX_REGISTRO` apontando para um arquivo temporário (~1 min). Rodar um teste sozinho também com essa variável.
- Teste isolado na obra real: `ARMANILUX_CONFIG` e `ARMANILUX_REGISTRO` apontando para arquivos temporários, `--workspace` e `--downloads` em pasta temporária, `--zip` com o zip de `Downloads` (624 MB).
- `run_pipeline.py --listar`; gerar: `--indice 1` ou `--todas`; remontar: `--rebuild-only --recalcular --obra-dir "<pasta da obra>"` (sem `--recalcular`, `eventos_adicionais` não entram); concluir: `--concluir --indice 1`.
- Depois de mudar a skill: mover a cópia instalada para `D:\_ai-archive\<data>\` (anotar em `COMO-RESTAURAR.md`) e copiar a pasta do repo para `.claude\skills`.
- PRs: squash merge depois do CI verde (`gh pr checks <n> --watch` em segundo plano). Depois de merge pelo `gh`, rode `git fetch` antes de comparar com `main`.
- Python inline em heredoc no Bash perde `\\`: escreva o script em arquivo (Write) e rode.
- Disco C: está 95% cheio.

## Arquivos-chave
- `C:\Users\EuSou\Documents\Armanilux\avaliacao-2026-11-19\0-resumo.md` — o que faltava para enviar ao Rogério ("Should fix soon" é a pendência 2).
- `skills/relatorio-cronologico-obra/scripts/run_pipeline.py` — entrada de tudo; `_preservar`, `_conversa_extraida`, `_gravar` (versão e rascunhos), `instalador_do_preparo`.
- `skills/relatorio-cronologico-obra/scripts/parse_whatsapp.py` — mensagens coladas (`_linha_colada`).
- `skills/relatorio-cronologico-obra/references/analise-json.md` — chaves do `analise.json` (`conversa`, `versao`, o que é preservado).
- `skills/relatorio-cronologico-obra/SKILL.md` — fluxo e revisão obrigatória do agente.
- `tests/test_reexportacao.py` — nova exportação, conversa sem mídia, versão fixa.
- `C:\Users\EuSou\Downloads\prompt.md` e o PDF 8665.1 V3 — referência do Rogério (fora do repo).

## Skills sugeridas
- `mattpocock-skills:tdd` — cada correção com teste antes.
- `mattpocock-skills:code-review` — antes de abrir cada PR.
- `relatorio-cronologico-obra` — para remontar a obra de teste (pendência 1).
