# HANDOFF — armanilux-relatorio-obra (2026-11-19)

## Estado atual
Duas skills na `main` (PRs #5 a #32; 138 testes; CI verde no Ubuntu e no Windows com Python 3.10, 3.12 e 3.13): `preparar-projeto-armanilux` 1.3 e `relatorio-cronologico-obra` 1.11. As duas instaladas em `C:\Users\EuSou\.claude\skills\`, iguais à `main`.
Os 6 bloqueadores da avaliação (`C:\Users\EuSou\Documents\Armanilux\avaliacao-2026-11-19\0-resumo.md`) foram corrigidos em #24–#27. O "deveria corrigir" e os pequenos que sobraram foram corrigidos em #29 (conferência bloqueia a final), #30 (áudio, Python, privacidade), #31 (avisos da execução) e #32 (obra/cliente, registro, textos).
Obra de teste (pasta em `Documents\Armanilux\Relatorios-de-Obra\`, FORA do repo): remontada com o código novo em 2026-11-19, saiu `v13` final ao lado do `v12` (123 de 123 fatos batem; `versao: 13` gravada; registro atualizado). O PDF não sai neste PC: o config antigo tem `gerar_pdf: true`, mas não há Word nem LibreOffice (o Word `.docx` é a entrega).

## Decisões desta sessão
- Nova exportação de obra já revisada volta a ser rascunho (`revisado` não é preservado); `eventos_adicionais`, ajustes e textos da revisão continuam. O script avisa para conferir as mensagens novas e a conclusão.
- `analise.json` guarda `conversa` (o `.txt` da última exportação lida). Sem essa marca (análise antiga), vale o `.txt` mais recente, não o maior.
- `analise.json` guarda `versao`. A final `vN` tem o número do rascunho e é regravada a cada remontagem (corrigir erro não gasta versão). `v2` só com conversa nova. Rascunhos da versão final vão para `05-relatorios/rascunhos/` (nada é apagado; nome repetido ganha `-2`). Final aberta no Word: o script pede para fechar e remontar.
- Obra antiga com `revisado: true` e sem `versao` (a obra de teste) ganha uma versão a mais uma única vez (v13) na primeira remontagem; depois fica fixa.
- Coladas no formato `[12:25, 03/07/2026] Nome:` agora viram mensagem com autor e hora originais. Na obra de teste: coladas reconhecidas 25 → 77, em 13 datas (antes 5). Segundos/AM-PM dentro do colchete colado e data mês/dia não são tratados (não aparecem nas conversas reais).
- Linha de colagem: se o `$skill-installer` não rodar (PC sem Python), baixar o zip com PowerShell e copiar as duas pastas; os comandos estão no AGENTS.md (TLS 1.2, sem trocar pasta que já existe). O instalador do preparo é achado pela pasta da própria skill (`run_pipeline.instalador_do_preparo()`; SKILL.md usa `<pasta-de-skills>`).
- `test_entrega` passa a usar registro temporário. Um teste rodado sozinho tinha gravado a obra fictícia 1001 no registro real; a entrada foi tirada (cópia em `D:\_ai-archive\2026-11-19\registro-antes-de-tirar-obra-1001-de-teste.json`).
- `"revisado": true` só vira versão final se a conferência rodou e `verificacao.md` não lista fato; senão sai rascunho e o script diz o motivo.
- "Não" aos áudios no preparo (`baixar_modelo_whisper: false`) vale no relatório: nada é baixado; `--transcrever` liga depois.
- Python aceito: 3.10 a 3.13 (fora disso o instalador instala 3.12). Bibliotecas com versão fixa (`requirements.txt` e a cópia do preparo, iguais). Ambiente de outro Python é guardado como `venv-antigo-<data>`. O venv deste PC é 3.14.3: será trocado na próxima preparação.
- Privacidade: os textos dizem que o ChatGPT (Codex) lê a conversa, os documentos e as fotos, e mandam desligar "Melhorar o modelo para todos".
- Conversa sem o aviso de criptografia nem a criação do grupo nas 3 primeiras mensagens = "parece cortada": aviso e lacuna. Na obra de teste não dispara. Quem entrou depois no grupo ou conversa em outro idioma também cai nisso (aceito).
- Folhas de contato: data da mensagem que anexou a foto; sem mensagem, a do nome com "(nome do arquivo)".
- Antes de gerar, o agente pergunta "Obra N, cliente X, certo?". Correção vai com `--indice N --obra --cliente` e fica no registro. "Obra 8977" no nome vale mais que outro número. A remontagem atualiza o registro.
- "Limites do material" no v13 está certo, não é erro: 64 arquivos com nome (56 PDFs) e 165 `<Mídia oculta>` não vieram porque o WhatsApp só põe no zip o que está baixado no celular que exporta (faltas espalhadas por todos os meses, não é corte). Vieram 180 mídias (118 fotos, 51 vídeos, 10 áudios, 1 figurinha); os quadros saem desses 51 vídeos (153 em `03-midias\quadros`). Os 4 `DP_DET …` são desenhos sem camada de texto (não há OCR). Ian: lista dos 64 faltantes não é necessária agora, é só teste.
- Estado combinado com o Ian: instalação e segurança prontas; texto do relatório ainda não está pronto para cliente (pendência 1).
- Antes já valiam: transcrição com cache por arquivo; entrega Word, PDF ou link escolhida no preparo; prazo contratual só com fonte escrita da época (`fonte_data`; posterior leva `*`); "dias" sem "úteis" = `dias_corridos`; cores marrom `#442819` e dourado `#C3A56D`.

## Não mexer
- A ideia central e as etapas A–L (sem K) do `prompt.md`; só melhorias pequenas.
- Formato compacto do PDF aprovado (8665.1 V3) e os gráficos atuais (Ian gostou).
- Pergunta de áudio no preparo ("Quer que eu também entenda os áudios e vídeos… cerca de 484 MB…").
- Não apagar dados sensíveis do relatório. Imagem é só contexto, sem descrição no relatório.
- Repo é PÚBLICO: nunca commitar nome de cliente, zip, conversa ou relatório real (`tests/test_skill.py` barra alguns nomes).
- Instalar skills só no app em uso (Codex → `.codex\skills`; Claude Code → `.claude\skills`).

## Pendências (em ordem)
1. Lacunas de qualidade do v13 (é o que o Rogério vai julgar; próxima tarefa): conclusão em 14/09 errada, intervalos misturando frentes, "programado" contado como feito, datas finais e total 304/302 que não batem, etapa J agrupada por tipo. Uma correção por vez, com teste antes; conferir depois remontando a obra de teste (`v13` é regravado, não vira v14).
2. Ian abrir o `v13` e comparar com o PDF aprovado. A remontagem não relê a conversa: as 77 coladas só entram numa exportação nova da obra.
3. Teste real no PC do Rogério (passos em `3-pronto-para-enviar.md`, "What Rogério must do himself"): é o único jeito de provar a instalação no Codex sem Python e a pasta de skills que o Codex usa.
4. Rodar `$preparar-projeto-armanilux` neste PC para trocar o venv 3.14 pelo 3.12 com as versões fixas (o antigo fica guardado).
5. Sobras aceitas de #29–#32 (só se incomodarem): "Cliente:" solto no grupo ainda vale mais que o nome do arquivo (a pergunta sim/não pega); remontar não refaz folhas de contato nem lacunas automáticas; instalador cortado na criação do venv pode deixar ambiente sem pip.
6. Limpar textos automáticos antigos de `analyze.py` que o Word compacto não usa.

## Como rodar
- Python: `C:\Users\EuSou\.armanilux-relatorio\venv\Scripts\python.exe` (config em `%USERPROFILE%\.armanilux-relatorio\config.json`).
- Testes: `python -m unittest discover -s tests` com `ARMANILUX_REGISTRO` apontando para um arquivo temporário (~2 min). Rodar um teste sozinho também com essa variável.
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
