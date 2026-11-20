# HANDOFF — armanilux-relatorio-obra (2026-11-20)

## Estado atual
Duas skills na `main` (PRs #5 a #46; 203 testes; CI verde no Ubuntu e no Windows com Python 3.10, 3.12 e 3.13): `preparar-projeto-armanilux` 1.4 e `relatorio-cronologico-obra` 1.13. As duas instaladas em `C:\Users\EuSou\.claude\skills\`, iguais à `main`.
Instalar pelo link funciona (#45, #46): a pessoa cola o link do repositório no Codex ou no Claude Code e escreve "instale aqui"; o agente segue o `INSTALL.md` (só PowerShell, sem Python). Provado no app ChatGPT (Codex, modo "Work", acesso total) em 20/11/2026: as skills vão para `%USERPROFILE%\.codex\skills` e aparecem num chat novo.
Teste do Codex NESTE PC pela metade: `$preparar-projeto-armanilux` começou às 01:28. Já fez: LibreOffice instalado; venv novo Python 3.11.15 com as bibliotecas (o antigo ficou como `venv-antigo-20261120-013135`). Não fez: gravar `config.json` (ainda o de 18/11, `"modelo_pasta_obra": "{cliente} - {numero}"`). O Codex encerrou o turno no meio da instalação do LibreOffice e não voltou sozinho.
Avaliação (fora do repo) em `C:\Users\EuSou\Documents\Armanilux\avaliacao-v13-2026-11-19\`: nota v13 8,5/10 (precisão 9,0); só o prompt 6,5; gabarito 30 de 30 (`gabarito-8977.1.json`, NUNCA no repo); `pesquisa-instalacao.md` (como repos famosos instalam por link).

## Decisões desta sessão
- Instalar pelo link: aviso bilíngue "Para o agente" no topo do README aponta para o `INSTALL.md` cru; Codex → `.codex\skills` (provado; não `.agents\skills`), Claude Code → `.claude\skills`; nunca nos dois; pasta que já existe não é trocada (renomear para `<nome>.antiga` só se pedirem para reinstalar).
- Preparo 1.4: pergunta do nome da pasta mostra exemplo em cada opção ("1001 - Família Almeida", "Família Almeida - 1001", "1001") e diz a atual com o exemplo dela (pedido do Ian).
- Rodada de precisão (#44) continua valendo: aprovação revista não é marco; fato em faixa (`data_evento_ate`); `quem_segurou`/`externo` no contrato; `dias_perdidos_armanilux` na etapa J; `"programado"` só para fato futuro, ação feita que não é marco leva `"marco": false`; conclusão só com `"conclusao": true` na etapa L. Detalhes em `skills/relatorio-cronologico-obra/references/analise-json.md`.
- Problema achado no teste: o Codex encerra o turno durante instalações longas; o Rogério não saberia que precisa escrever "continue". Corrigir na skill (pendência 3).

## Não mexer
- A ideia central e as etapas A–L (sem K) do `prompt.md`; só melhorias pequenas.
- Formato compacto do PDF aprovado (8665.1 V3) e os gráficos atuais (Ian gostou).
- Pergunta de áudio no preparo ("Quer que eu também entenda os áudios e vídeos… cerca de 484 MB…").
- Não apagar dados sensíveis do relatório. Imagem é só contexto, sem descrição no relatório.
- Repo é PÚBLICO: nunca commitar nome de cliente, zip, conversa, citação da conversa ou relatório real (`tests/test_skill.py` barra alguns nomes). Exemplos nas skills sempre genéricos.
- Instalar skills só no app em uso.

## Pendências (em ordem)
1. Terminar o teste do Codex: Ian escreve no chat do Codex "pode continuar e terminar a configuração" (grava `config.json`). Depois, chat novo com `$relatorio-cronologico-obra`, o zip da obra de teste e `--workspace C:\Users\EuSou\Documents\Armanilux-teste-codex\Relatorios-de-Obra`, até `"revisado": true`.
2. Pontuar o resultado do Codex: `tools/pontuar_relatorio.py --gabarito "C:\Users\EuSou\Documents\Armanilux\avaliacao-v13-2026-11-19\gabarito-8977.1.json" --obra-dir <pasta da obra do Codex>` e comparar com o 30/30 do Claude. Depois restaurar `registro.json` (e `config.json`, se o Ian quiser o modelo antigo `{cliente} - {numero}`) de `D:\_ai-archive\2026-11-20\armanilux-relatorio-config-antes-codex\`.
3. Nas duas SKILL.md: mandar o agente esperar cada instalação terminar e não encerrar o turno no meio (visto no Codex). Junto, enxugar a SKILL.md do relatório (Ian perguntou se precisa de tanta orientação): manter o passo a passo curto e mover detalhes para `references/`. A skill já deve achar sozinha o zip do WhatsApp (Ian quer isso; conferir que funciona no Codex).
4. Antes de enviar ao Rogério: escrever no README os cliques do app (ChatGPT → Codex, modo "Work", acesso total); depois, teste supervisionado no PC dele.
5. Sobras da nota (`nota-v13-nova.md`, só se valer): dias sem frente talvez baixos (15–19/06); etapa C sem 09/04, 16/04 e 13/05; living 13/05 → 22/05 = 7 de 6 d.u. fora do contrato; críticas da arquitetura à Armanilux; lavanderia (pedra natural) na regra de 25 d.u.; aprovação do gourmet em 14/10 não explícita; recomendações; coluna "d.u. desde o evento anterior".
6. Limpar textos automáticos antigos de `analyze.py` que o Word compacto não usa (`_comentarios_etapa`, `_conclusao`, `_gargalos`…).

## Como rodar
- Python: `C:\Users\EuSou\.armanilux-relatorio\venv\Scripts\python.exe` (agora 3.11, refeito pelo Codex; config em `%USERPROFILE%\.armanilux-relatorio\config.json`).
- Testes: `python -m unittest discover -s tests` com `ARMANILUX_REGISTRO` apontando para um arquivo temporário (~1 min).
- Remontar a obra de teste: `run_pipeline.py --rebuild-only --recalcular --obra-dir "<pasta da obra>"`.
- Depois de mudar a skill: mover a cópia instalada para `D:\_ai-archive\<data>\` (anotar em `COMO-RESTAURAR.md`) e copiar a pasta do repo para `.claude\skills`.
- PRs: squash merge depois do CI verde. Depois de merge pelo `gh`, `git fetch` antes de comparar com `main`.
- Python inline em heredoc no Bash perde `\`: escreva o script em arquivo (Write) e rode. Gravar arquivos com `write_bytes` (o `write_text` vira CRLF no Windows); `.bat` precisa de CRLF.
- Disco C: está 95% cheio.

## Arquivos-chave
- `INSTALL.md` e o topo do `README.md` — instalação pelo link (para o agente).
- `skills/preparar-projeto-armanilux/SKILL.md` e `scripts/instalar.ps1` — preparo do PC.
- `skills/relatorio-cronologico-obra/SKILL.md` e `references/analise-json.md` — revisão e campos.
- `tools/pontuar_relatorio.py` — gabarito.
- `D:\_ai-archive\2026-11-20\COMO-RESTAURAR.md` — tudo que foi movido hoje (skills antigas, config antes do Codex, v13 antes da precisão).

## Skills sugeridas
- `mattpocock-skills:writing-for-agents` — para enxugar as SKILL.md (pendência 3).
- `mattpocock-skills:tdd` e `mattpocock-skills:code-review` — em qualquer correção nova.
- `relatorio-cronologico-obra` — para remontar ou revisar a obra de teste.
