# HANDOFF — armanilux-relatorio-obra (2026-11-19)

## Estado atual
Duas skills na `main` (PRs #5 a #8 mergeados): `preparar-projeto-armanilux` (perguntas + instalação) e `relatorio-cronologico-obra` (zip do WhatsApp → Word).
Já funciona: busca automática do zip (nome com acento e parênteses), registro por SHA-256 (pendente → em andamento → relatório gerado → concluído), PDFs em ~25 s, transcrição local de áudio e vídeo, não duplica arquivos ao reprocessar, candidatos por etapa, folhas de contato (12 miniaturas por folha), capa, quadro-resumo, cores da marca, faixa "RASCUNHO NÃO REVISADO" até a revisão gravar `"revisado": true`.
Teste real feito com uma obra de ~595 MB (pasta em `Documents\Armanilux\Relatorios-de-Obra\`, FORA do repo).

### Sessão 2026-11-19 — 4 branches empilhadas, NÃO enviadas ao GitHub
O push e o PR foram barrados pelo guarda de permissão (publicar exige o Ian). Ordem: `midia-oculta-e-reencaminhadas` → `graficos-legiveis` → `contexto-completo` → `relatorio-compacto` (cada uma parte da anterior; `relatorio-compacto` tem tudo). 72 testes passando.
- Pendências 2 e 3 feitas: nome do arquivo em "<Mídia oculta>" (64 na obra de teste) com "(arquivo não incluído na exportação)"; mensagem colada `[dd/mm, hh:mm] Nome:` vai para a data e o autor originais (25 mensagens, 5 blocos), sem esticar o período.
- Pendência 4 feita: marco = primeiro registro de cada etapa; tabela e Figura 1 com um intervalo por marco + duração total, sem semáforo (52 barras → 9). Gráficos desenhados a 16,2 cm (letra não encolhe), Gantt sem borda vermelha.
- Pedido do Ian (contexto): SKILL.md 1.3 manda ler a conversa inteira, todas as transcrições, documentos e imagens; seção "Lacunas de contexto" no Word; `verificacao.py` confere cada fato contra a conversa (grava `04-transcricoes/verificacao.md`); conferência independente de conteúdo por subagente antes de `revisado`. "Anexo de mídias" (tabela de nomes) virou "Registro fotográfico" (só imagens descritas). Planilha `.xlsx` passa a ser lida.
- No v6: só 2 de 169 fotos/vídeos tinham descrição e os documentos não eram lidos pelo agente — por isso a mudança acima. As 70 datas/autores do v6 batem com o grupo.
- Ian viu o v7: texto demais, registro fotográfico inútil, descrição de imagem pelo agente é imprecisa. Virou `relatorio-compacto` (SKILL 1.4): mesmo formato do 8665.1 V3 — Nota Metodológica (com limites do material e convenção de cores), Quadro-Resumo, etapas A–L com tabela Data | Evento de uma frase por linha (salmão = reprocesso, amarelo = ocioso; `destaque_auto` sugere, a revisão troca com `destaque`), "Leitura da Etapa", Análise de Prazos (d.u. em vermelho), Diagnóstico em 5 blocos de tópicos, Conclusão Estratégica. Imagem é só contexto para o agente.
- Prazo contratual: Ian pediu para usar quando houver. A revisão grava `prazos_contratuais` (só o que está escrito no grupo ou em documento, com fonte); o Word mostra o confronto Contrato × Realizado em vermelho e os prazos na Nota. Na obra de teste os prazos estão na mensagem de abertura do grupo (29/08/2025) e no orçamento 8977.8.v1 — os mesmos 4 do PDF do Guilherme.
- Word v9 da obra de teste (layout compacto + prazos; backups `analise.antes-v7.json` e `analise.antes-v8.json`): 4.318 palavras (v7: 6.730; PDF do Guilherme: 4.359). Os textos ainda são os da revisão antiga (v6) — falta a revisão completa da SKILL 1.4.

## Decisões desta sessão
- Seguir o `prompt.md` do Rogério; só melhorias pequenas, sem decidir nada por ele — pedido do Ian.
- Não apagar dados sensíveis (telefone, CPF, banco) do relatório — ele só vai para o grupo e clientes.
- Prazo contratual (mudou em 19/11, pedido do Ian): usar quando o grupo ou um documento declara; nunca deduzir. Sem declaração, fica "dado não identificado".
- Formato de referência: relatório da obra 8665.1 V3 (PDF em `C:\Users\EuSou\Downloads\`), aprovado pelo Rogério; dá para melhorar sem quebrar.
- Capa, quadro-resumo e confronto com o contrato seguem o PDF aprovado. O relatório é curto: o contexto inteiro é para o agente, não para o Word (pedido do Ian).
- Cores: marrom `#442819` e dourado `#C3A56D` (site armanilux.com.br).
- O agente que roda a skill faz a revisão obrigatória (candidatos + folhas de contato + transcrições); o código é só pré-filtro.
- `8977.1.v10`: o `.vNN` é versão, o número da obra fica `8977.1`.
- Instalar skills só no app em uso (Codex → `.codex\skills`; Claude Code → `.claude\skills`).

## Não mexer
- A ideia central e as etapas A–L (sem K) do `prompt.md`.
- Pergunta de áudio no preparo ("Quer que eu também entenda os áudios e vídeos… cerca de 484 MB…").
- Repo é PÚBLICO: nunca commitar nome de cliente, zip, conversa ou relatório real (`tests/test_skill.py` barra alguns nomes).

## Pendências (em ordem)
1. Ian liberar o push das 4 branches e abrir os PRs (ou mandar abrir); merge na ordem acima.
2. Ian abrir o v9 e comparar com o PDF do Guilherme.
3. Rodar a revisão completa da SKILL 1.4 na obra de teste (ler tudo, frases curtas, cores, leituras, diagnóstico em tópicos, prazos com `inicio`/`fim` por frente, conferência independente). Hoje o confronto usa o primeiro registro de cada etapa, que numa obra de várias frentes é aproximado (ex.: medição 29 d.u., entrega 126 d.u.). Reprocessar do zip para os eventos usarem as datas originais das mensagens coladas.
4. Instalação: linha de colagem citando `$skill-installer` e as URLs `/tree/main/skills/<nome>` (README, AGENTS.md).
5. Transcrição com cache por arquivo (não refazer tudo), e rodar em segundo plano.
6. `analyze.py` ainda calcula textos automáticos antigos (`_impacto`, `_produtividade`, `_comentarios_etapa`, gargalos, responsabilidades) que o Word compacto não usa mais; limpar.

## Como rodar
- Python: `C:\Users\EuSou\.armanilux-relatorio\venv\Scripts\python.exe` (config em `%USERPROFILE%\.armanilux-relatorio\config.json`).
- Testes: `python -m unittest discover -s tests` (defina `ARMANILUX_REGISTRO` para um arquivo temporário).
- Listar conversas: `run_pipeline.py --listar`; gerar: `--indice 1` ou `--todas`; remontar após revisão: `--rebuild-only --recalcular --obra-dir "<pasta da obra>"`; concluir: `--concluir --indice 1`.
- Skill instalada para teste: `C:\Users\EuSou\.claude\skills\relatorio-cronologico-obra` (copiar a pasta do repo por cima depois de mudar).
- Comandos Python em heredoc no Bash perdem `\\` (vira `\n`, `\b`): edite código com Edit/Write, não com script inline.

## Arquivos-chave
- `skills/relatorio-cronologico-obra/SKILL.md` — fluxo e revisão obrigatória do agente.
- `skills/relatorio-cronologico-obra/scripts/run_pipeline.py` — entrada de tudo.
- `skills/relatorio-cronologico-obra/scripts/build_docx.py` — formato do Word.
- `skills/relatorio-cronologico-obra/scripts/analyze.py` — etapas, intervalos, textos.
- `C:\Users\EuSou\Downloads\prompt.md` e o PDF 8665.1 V3 — referência do Rogério (fora do repo).

## Skills sugeridas
- `mattpocock-skills:tdd` — cada pendência com teste antes.
- `mattpocock-skills:code-review` — antes de abrir cada PR.
- `relatorio-cronologico-obra` — para testar de ponta a ponta na obra real.
