# HANDOFF — armanilux-relatorio-obra (2026-11-19)

## Estado atual
Duas skills na `main` (PRs #5 a #22; 105 testes; CI verde no Ubuntu e no Windows): `preparar-projeto-armanilux` 1.2 (perguntas + instalação) e `relatorio-cronologico-obra` 1.9 (zip do WhatsApp → Word). As duas estão instaladas em `C:\Users\EuSou\.claude\skills\`, iguais à `main`.
Relatório no formato compacto do PDF aprovado (8665.1 V3). Obra de teste (pasta em `Documents\Armanilux\Relatorios-de-Obra\`, FORA do repo): v12 revisado, 123 fatos conferidos com o grupo.
Avaliação "pronto para enviar ao Rogério" feita nesta sessão (4 subagentes independentes): **ainda não está pronto**. Resumo e relatórios em `C:\Users\EuSou\Documents\Armanilux\avaliacao-2026-11-19\` (`0-resumo.md` primeiro; `1-nota-contra-prompt.md`, `2-execucao-real.md`, `3-pronto-para-enviar.md` têm arquivo:linha e sugestão de correção).

## Decisões desta sessão
- Transcrição com cache por arquivo (`04-transcricoes/transcricoes-cache.json`: SHA-256, modelo e texto). Arquivo igual não volta ao Whisper; execução interrompida continua; `--skip-transcribe` mantém o que já existe. Teste real: 1ª execução 21 min, 2ª 1,5 min.
- Entrega escolhida no preparo (`formato_entrega`: `word`, `pdf` ou `link`; config antigo com `gerar_pdf` vira pdf). PDF pelo Word (COM) ou LibreOffice; `instalar.ps1 -Pdf` instala o LibreOffice quando não há nenhum. Link: só a versão revisada (nunca rascunho) é copiada para a pasta do OneDrive/Google Drive (`pasta_link`; `preparar.py --listar-nuvens`; com as duas, a skill pergunta). Compartilhar só com pessoas específicas: o relatório tem dados do cliente. Conversão real para PDF não testada (este PC não tem Word nem LibreOffice).
- Linha de colagem da instalação: `$skill-installer instale estas skills:` + os dois endereços `/tree/main/skills/<nome>`. Linha antiga continua valendo pelo AGENTS.md. Não testada no Codex.
- v12: autorização da banheira movida para 03/11 19:04 e fato novo de 21/08 (desocupar cozinha e copa), a pedido do Ian. v12 anterior em `D:\_ai-archive\2026-11-19\v12-antes-ajuste-coladas\`.
- Mensagens coladas: no v12 nenhum fato usa a data da colagem. Atenção: o parser só reconhece `[03/07, 12:25] Nome:`; o formato `[12:25, 03/07/2026] Nome:` (45 linhas na obra de teste) passa despercebido. No v12 todas essas foram coladas no mesmo dia, então as datas do v12 estão certas.
- Antes já valiam: rascunho `-vN-rascunho.docx` regravado; `vN` só com `"revisado": true`; prazo contratual só com fonte escrita da época (`fonte_data`; posterior leva `*`); "dias" sem "úteis" = `dias_corridos`; cores marrom `#442819` e dourado `#C3A56D`.

## Não mexer
- A ideia central e as etapas A–L (sem K) do `prompt.md`; só melhorias pequenas.
- Formato compacto do PDF aprovado (8665.1 V3) e os gráficos atuais (Ian gostou).
- Pergunta de áudio no preparo ("Quer que eu também entenda os áudios e vídeos… cerca de 484 MB…").
- Não apagar dados sensíveis do relatório. Imagem é só contexto, sem descrição no relatório.
- Repo é PÚBLICO: nunca commitar nome de cliente, zip, conversa ou relatório real (`tests/test_skill.py` barra alguns nomes).
- Instalar skills só no app em uso (Codex → `.codex\skills`; Claude Code → `.claude\skills`).

## Pendências (em ordem)
1. Corrigir os 6 bloqueadores de `avaliacao-2026-11-19\0-resumo.md`, um PR por grupo, com teste antes:
   1. Nova exportação de obra já revisada sai como versão final sem revisão (`run_pipeline.py` `_preservar` mantém `revisado`; só junta `eventos_adicionais` quando há `ajustes_eventos`).
   2. Reexportação sem mídia usa a conversa antiga (`_conversa_extraida` escolhe o maior `.txt`).
   3. PC sem Python: a linha de colagem precisa de alternativa (baixar o zip do repo com PowerShell e copiar as duas pastas).
   4. Caminho fixo `.codex\skills\preparar-projeto-armanilux` (`SKILL.md` do relatório e `run_pipeline.py`): achar a partir da pasta da própria skill.
   5. Parser de coladas no formato `[HH:MM, DD/MM/AAAA] Nome:` (`parse_whatsapp.py` `_LINHA_ENCAMINHADA`), e a verificação aceitar o autor e a hora originais.
   6. Depois de `"revisado": true`, cada remontagem cria nova versão; o passo a passo entrega v2 como primeira aprovada.
2. "Deveria corrigir" do `0-resumo.md` (verificação pendente bloqueando versão final, confirmar obra/cliente com sim/não, respeitar "não" do áudio, travar versão do Python e das bibliotecas, texto de privacidade honesto, aviso de exportação cortada, datas das fotos pela mensagem, aviso de "pode levar alguns minutos" ao carregar o modelo, tempo limite de comandos longos).
3. Lacunas de qualidade do v12 (conclusão em 14/09 errada, intervalos misturando frentes, "programado" contado como feito, datas finais e total 304/302, etapa J por tipo).
4. Ian abrir o v12 e comparar com o PDF aprovado. Depois, teste real no PC do Rogério (passos em `3-pronto-para-enviar.md`, "What Rogério must do himself").
5. Limpar textos automáticos antigos de `analyze.py` que o Word compacto não usa.

## Como rodar
- Python: `C:\Users\EuSou\.armanilux-relatorio\venv\Scripts\python.exe` (config em `%USERPROFILE%\.armanilux-relatorio\config.json`).
- Testes: `python -m unittest discover -s tests` com `ARMANILUX_REGISTRO` apontando para um arquivo temporário (~1 min).
- Teste isolado na obra real: `ARMANILUX_CONFIG` e `ARMANILUX_REGISTRO` apontando para arquivos temporários, `--workspace` e `--downloads` em pasta temporária, `--zip` com o zip de `Downloads` (624 MB).
- `run_pipeline.py --listar`; gerar: `--indice 1` ou `--todas`; remontar: `--rebuild-only --recalcular --obra-dir "<pasta da obra>"`; concluir: `--concluir --indice 1`.
- Depois de mudar a skill: mover a cópia instalada para `D:\_ai-archive\<data>\` (anotar em `COMO-RESTAURAR.md`) e copiar a pasta do repo para `.claude\skills`.
- PRs: squash merge depois do CI verde (`gh pr checks <n> --watch` em segundo plano).
- Python inline em heredoc no Bash perde `\\`: escreva o script em arquivo (Write) e rode.
- Disco C: está 95% cheio. O teste real da avaliação (1,2 GB) foi movido para `D:\_ai-archive\2026-11-19\teste-real-avaliacao\`.

## Arquivos-chave
- `C:\Users\EuSou\Documents\Armanilux\avaliacao-2026-11-19\0-resumo.md` — o que falta para enviar ao Rogério.
- `skills/relatorio-cronologico-obra/scripts/run_pipeline.py` — entrada de tudo; `_preservar`, `_conversa_extraida`, `_gravar` (entrega).
- `skills/relatorio-cronologico-obra/scripts/parse_whatsapp.py` — mensagens coladas.
- `skills/relatorio-cronologico-obra/scripts/entrega.py` e `skills/preparar-projeto-armanilux/scripts/preparar.py` — Word, PDF ou link.
- `skills/relatorio-cronologico-obra/SKILL.md` — fluxo e revisão obrigatória do agente.
- `C:\Users\EuSou\Downloads\prompt.md` e o PDF 8665.1 V3 — referência do Rogério (fora do repo).

## Skills sugeridas
- `mattpocock-skills:tdd` — cada bloqueador com teste antes.
- `mattpocock-skills:code-review` — antes de abrir cada PR.
- `relatorio-cronologico-obra` — para testar de ponta a ponta na obra real.
