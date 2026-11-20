# HANDOFF — armanilux-relatorio-obra (2026-11-20)

## Estado atual
Duas skills na `main` (PRs #5 a #53; 228 testes; CI verde no Ubuntu e no Windows com Python 3.10, 3.12 e 3.13): `preparar-projeto-armanilux` 1.6 e `relatorio-cronologico-obra` 1.18. As duas instaladas em `C:\Users\EuSou\.claude\skills\`, iguais à `main`.
Instalar pelo link funciona (#45, #46): a pessoa cola o link do repositório no Codex ou no Claude Code e escreve "instale aqui"; o agente segue o `INSTALL.md` (só PowerShell, sem Python). Provado no app ChatGPT (Codex, modo "Work", acesso total) em 20/11/2026: as skills vão para `%USERPROFILE%\.codex\skills` e aparecem num chat novo.
Teste do Codex NESTE PC pela metade: `$preparar-projeto-armanilux` começou às 01:28. Já fez: LibreOffice instalado; venv novo Python 3.11.15 com as bibliotecas (o antigo ficou como `venv-antigo-20261120-013135`). Não fez: gravar `config.json` (ainda o de 18/11, `"modelo_pasta_obra": "{cliente} - {numero}"`). O Codex encerrou o turno no meio da instalação do LibreOffice e não voltou sozinho.
Os 6 bloqueadores da avaliação de 19/11 seguem corrigidos (#24-#27, conferido de novo em 20/11).
Prontidão para o Rogério, nova avaliação (fora do repo) em `C:\Users\EuSou\Documents\Armanilux\avaliacao-2026-11-20\` (`0-resumo.md` primeiro): caminho feliz funciona; os 4 bloqueadores novos foram corrigidos em #50 (final vazia), #51 (lista estável, pasta da obra), #53 (datas) e #52 (instalador), cada um com revisão em dois eixos.
Modelo do Rogério: ele mandou ao Ian o relatório que gosta (uma obra real, saída do ChatGPT comum). Comparação e recomendação em `avaliacao-2026-11-20\4-modelo-do-rogerio.md` (o txt NÃO está salvo; é obra real, nunca no repo).
O Word final v13 da obra de teste foi enviado ao Google Drive do Ian (Meu Drive, privado) em 20/11.
Avaliação de qualidade (fora do repo) em `C:\Users\EuSou\Documents\Armanilux\avaliacao-v13-2026-11-19\`: nota v13 8,5/10 (precisão 9,0); só o prompt 6,5; gabarito 30 de 30 (`gabarito-8977.1.json`, NUNCA no repo); `pesquisa-instalacao.md` (como repos famosos instalam por link).

## Decisões desta sessão
- Instalar pelo link: aviso bilíngue "Para o agente" no topo do README aponta para o `INSTALL.md` cru; Codex → `.codex\skills` (provado; não `.agents\skills`), Claude Code → `.claude\skills`; nunca nos dois; pasta que já existe não é trocada (renomear para `<nome>.antiga` só se pedirem para reinstalar).
- Preparo 1.4: pergunta do nome da pasta mostra exemplo em cada opção ("1001 - Família Almeida", "Família Almeida - 1001", "1001") e diz a atual com o exemplo dela (pedido do Ian).
- Rodada de precisão (#44) continua valendo: aprovação revista não é marco; fato em faixa (`data_evento_ate`); `quem_segurou`/`externo` no contrato; `dias_perdidos_armanilux` na etapa J; `"programado"` só para fato futuro, ação feita que não é marco leva `"marco": false`; conclusão só com `"conclusao": true` na etapa L. Detalhes em `skills/relatorio-cronologico-obra/references/analise-json.md`.
- #48: o agente fica no turno até o comando mostrar o código de saída; se a resposta tiver de acabar antes, a última linha é `Escreva "continue" para eu terminar.` (nas duas skills).
- #50: a versão final só sai sem nenhum "preencher na revisão" no Word (5 listas do diagnóstico, pontos críticos, conclusão, recomendações) e com o prazo contratual respondido (`prazos_contratuais` ou a lacuna "Prazo contratual não declarado..."); regra em `build_docx.textos_que_faltam`. Rascunho imprime "RASCUNHO: não envie". Testes que marcam revisado usam `REVISAO_COMPLETA` de `examples/gerar_exemplo.py`.
- #51: `--indice` usa a lista do último `--listar` (`registro.fixar_lista`); mesma obra com cliente escrito de outro jeito reaproveita a pasta (só se houver uma; duas avisam); "(1)", `_chat` e ano solto não viram cliente/número (ano sozinho ainda vale: pode ser a obra 2010).
- #53: ordem dia/mês por arquivo, provada por número acima de 12 ou zero na frente ("03/07" é dia/mês; EUA escreve "7/3/26"); AM/PM não prova; sem prova, `data_incerta` e lacuna automática.
- #52: `instalar.ps1` confere disco (bloqueia com menos de 3 GB só quando falta instalar Python ou o venv) e abre as bibliotecas depois do pip (VC++ se falhar); `config_io.pasta_documentos`/`pasta_armanilux_padrao` usam a Documentos real (OneDrive), e quem já tem `Documents\Armanilux` continua nela.
- #48: SKILL.md do relatório enxuta (~2.000 palavras, teste limita a 2.200); as regras da revisão (4.1-4.5) estão em `references/revisao.md`, sem mudança de conteúdo.

## Não mexer
- A ideia central e as etapas A–L (sem K) do `prompt.md`; só melhorias pequenas.
- Formato compacto do PDF aprovado (8665.1 V3) e os gráficos atuais (Ian gostou).
- Pergunta de áudio no preparo ("Quer que eu também entenda os áudios e vídeos… cerca de 484 MB…").
- Não apagar dados sensíveis do relatório. Imagem é só contexto, sem descrição no relatório.
- Repo é PÚBLICO: nunca commitar nome de cliente, zip, conversa, citação da conversa ou relatório real (`tests/test_skill.py` barra alguns nomes). Exemplos nas skills sempre genéricos.
- Instalar skills só no app em uso.

## Pendências (em ordem)
1. Modelo do Rogério: Ian decide quais itens de `avaliacao-2026-11-20\4-modelo-do-rogerio.md` entram no Word (recomendação: legenda de classificação, linha Status por etapa, etapa L como lista do que falta provar, coluna Interpretação nos intervalos, selo por tema no diagnóstico, recomendações em tabela com prioridade). Os itens que mexem no topo do formato 8665.1 V3 (resumo executivo, destaque de previsto) só com o sim do Ian. Para usar o txt de modelo, salvar nessa pasta.
2. Terminar o teste do Codex: Ian escreve no chat do Codex "pode continuar e terminar a configuração" (grava `config.json`). Depois, chat novo com `$relatorio-cronologico-obra`, o zip da obra de teste e `--workspace C:\Users\EuSou\Documents\Armanilux-teste-codex\Relatorios-de-Obra`, até `"revisado": true`. Ver se a regra do "continue" (#48) funciona.
3. Pontuar o resultado do Codex: `tools/pontuar_relatorio.py --gabarito "C:\Users\EuSou\Documents\Armanilux\avaliacao-v13-2026-11-19\gabarito-8977.1.json" --obra-dir <pasta da obra do Codex>` e comparar com o 30/30 do Claude. Depois restaurar `registro.json` (e `config.json`, se o Ian quiser o modelo antigo `{cliente} - {numero}`) de `D:\_ai-archive\2026-11-20\armanilux-relatorio-config-antes-codex\`.
4. Revisão em Codex sem subagentes (grupo de 15 meses não cabe): transcrições e documentos em arquivos por trimestre, `revisao-progresso.md` para continuar entre "continue", resposta final diz quanto foi lido; registrar que a conferência independente (4.4) rodou. Precisa de desenho antes.
5. Antes de enviar ao Rogério: Ian manda captura da tela do app (ChatGPT → Codex, modo "Work", acesso total) para escrever os cliques no README; depois, teste supervisionado no PC dele (usuário com acento, winget/UAC no Codex, antivírus, 40 min no turno, Documentos no OneDrive, transcrição na CPU dele).
6. Sobras: instalador sem winget ainda só explica e para (instalar o winget sozinho); "Mostre esta mensagem ao Ian" no `instalar.ps1`. Da nota (`nota-v13-nova.md`, só se valer): dias sem frente talvez baixos (15–19/06); etapa C sem 09/04, 16/04 e 13/05; living 13/05 → 22/05 = 7 de 6 d.u. fora do contrato; críticas da arquitetura à Armanilux; lavanderia (pedra natural) na regra de 25 d.u.; aprovação do gourmet em 14/10 não explícita; recomendações; coluna "d.u. desde o evento anterior". Também: fato J acrescentado sem autor no Word; etapa J repete fatos de H e I.
7. Limpar textos automáticos antigos de `analyze.py` que o Word compacto não usa (`_comentarios_etapa`, `_conclusao`, `_gargalos`…).

## Como rodar
- O app pode trocar o branch entre um comando e outro (segue o PR que está vigiando): confira `git branch --show-current` antes de cada commit.
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
- `mattpocock-skills:writing-for-agents` — para mudar SKILL.md ou references (pendência 4).
- `mattpocock-skills:tdd` e `mattpocock-skills:code-review` — em qualquer correção nova.
- `relatorio-cronologico-obra` — para remontar ou revisar a obra de teste.
