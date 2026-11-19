# HANDOFF — armanilux-relatorio-obra (2026-11-19)

## Estado atual
Duas skills na `main` (PRs #5 a #8 mergeados): `preparar-projeto-armanilux` (perguntas + instalação) e `relatorio-cronologico-obra` (zip do WhatsApp → Word).
Já funciona: busca automática do zip (nome com acento e parênteses), registro por SHA-256 (pendente → em andamento → relatório gerado → concluído), PDFs em ~25 s, transcrição local de áudio e vídeo, não duplica arquivos ao reprocessar, candidatos por etapa, folhas de contato (12 miniaturas por folha), capa, quadro-resumo, cores da marca, faixa "RASCUNHO NÃO REVISADO" até a revisão gravar `"revisado": true`.
Teste real feito com uma obra de ~595 MB (pasta em `Documents\Armanilux\Relatorios-de-Obra\`, FORA do repo).

### Sessão 2026-11-19 (tarde) — 3 branches empilhadas, NÃO enviadas ao GitHub
O push e o PR foram barrados pelo guarda de permissão (publicar exige o Ian). Ordem: `midia-oculta-e-reencaminhadas` → `graficos-legiveis` → `contexto-completo` (cada uma parte da anterior; `contexto-completo` tem tudo). 65 testes passando.
- Pendências 2 e 3 feitas: nome do arquivo em "<Mídia oculta>" (64 na obra de teste) com "(arquivo não incluído na exportação)"; mensagem colada `[dd/mm, hh:mm] Nome:` vai para a data e o autor originais (25 mensagens, 5 blocos), sem esticar o período.
- Pendência 4 feita: marco = primeiro registro de cada etapa; tabela e Figura 1 com um intervalo por marco + duração total, sem semáforo (52 barras → 9). Gráficos desenhados a 16,2 cm (letra não encolhe), Gantt sem borda vermelha.
- Pedido do Ian (contexto): SKILL.md 1.3 manda ler a conversa inteira, todas as transcrições, documentos e imagens; seção "Lacunas de contexto" no Word; `verificacao.py` confere cada fato contra a conversa (grava `04-transcricoes/verificacao.md`); conferência independente de conteúdo por subagente antes de `revisado`. "Anexo de mídias" (tabela de nomes) virou "Registro fotográfico" (só imagens descritas). Planilha `.xlsx` passa a ser lida.
- No v6: só 2 de 169 fotos/vídeos tinham descrição e os documentos não eram lidos pelo agente — por isso a mudança acima. As 70 datas/autores do v6 batem com o grupo.
- Word v7 da obra de teste gerado com o código da `contexto-completo` (backup em `04-transcricoes/analise.antes-v7.json`). Skill instalada em `.claude\skills` já é a 1.3.

## Decisões desta sessão
- Seguir o `prompt.md` do Rogério; só melhorias pequenas, sem decidir nada por ele — pedido do Ian.
- Não apagar dados sensíveis (telefone, CPF, banco) do relatório — ele só vai para o grupo e clientes.
- Não perguntar nem tratar prazo contratual — eles resolvem entre eles; fica "dado não identificado".
- Formato de referência: relatório da obra 8665.1 V3 (PDF em `C:\Users\EuSou\Downloads\`), aprovado pelo Rogério; dá para melhorar sem quebrar.
- Capa e quadro-resumo entram (vêm do PDF aprovado, não do prompt); "Confronto com o contrato" fica de fora.
- Cores: marrom `#442819` e dourado `#C3A56D` (site armanilux.com.br).
- O agente que roda a skill faz a revisão obrigatória (candidatos + folhas de contato + transcrições); o código é só pré-filtro.
- `8977.1.v10`: o `.vNN` é versão, o número da obra fica `8977.1`.
- Instalar skills só no app em uso (Codex → `.codex\skills`; Claude Code → `.claude\skills`).

## Não mexer
- A ideia central e as etapas A–L (sem K) do `prompt.md`.
- Pergunta de áudio no preparo ("Quer que eu também entenda os áudios e vídeos… cerca de 484 MB…").
- Repo é PÚBLICO: nunca commitar nome de cliente, zip, conversa ou relatório real (`tests/test_skill.py` barra alguns nomes).

## Pendências (em ordem)
1. Ian liberar o push das 3 branches e abrir os PRs (ou mandar abrir); merge na ordem acima.
2. Ian abrir o v7 e dar retorno sobre gráficos, Lacunas e Registro fotográfico.
3. Rodar a revisão completa da SKILL 1.3 na obra de teste (ler tudo, descrever imagens, conferência independente) e gerar v8 — o v7 ainda usa a revisão antiga (2 imagens descritas). Reprocessar do zip para os eventos usarem as datas originais das mensagens coladas.
4. Linhas das etapas coloridas como no PDF (salmão = reprocesso, amarelo = ocioso) e uma frase objetiva por evento.
5. Instalação: linha de colagem citando `$skill-installer` e as URLs `/tree/main/skills/<nome>` (README, AGENTS.md).
6. Transcrição com cache por arquivo (não refazer tudo), e rodar em segundo plano.
7. Textos automáticos genéricos em `analyze.py` (`_impacto`, `_produtividade`, `_comentarios_etapa`) ainda afirmam coisas; trocar por "dado não identificado" quando não houver revisão.

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

### Em andamento (branch `relatorio-compacto`, commit WIP, testes antigos ainda falhando)
Pedido do Ian: relatório compacto como o PDF 8665.1 V3 (Nota Metodológica → Quadro-Resumo → etapas A–L com tabela Data | Evento curta, linha salmão = reprocesso / amarela = ocioso, "Leitura da Etapa X" → Análise de Prazos com d.u. em vermelho acima de 20 → Diagnóstico em 5 blocos de marcadores → Conclusão Estratégica). Sem registro fotográfico e sem descrição de imagens: imagem serve só de contexto para o agente.
Feito: `tests/test_formato_compacto.py` (6 testes, passando), `destaque_automatico`, `LIMITE_INTERVALO_LONGO`, novo `build_docx` (seções compactas), lacunas curtas na Nota Metodológica.
Falta: (1) atualizar testes antigos (`test_anexo` RegistroFotograficoTeste → apagar; `test_lacunas` Word → olhar "Limites do material"; `test_marcos` linha total agora "DURAÇÃO TOTAL REGISTRADA"; `test_pipeline` lista de trechos); (2) SKILL.md: ocorrência = 1 frase ≤ 25 palavras, campo `destaque`, `comentarios.X.introducao/leitura`, `diagnostico_prompt` em listas + `interferencias`, `pontos_criticos`, `impactos_prazo`, imagens só como contexto (tirar observacoes_visuais do fluxo); (3) formato-relatorio.md e analise-json.md; (4) remover import `WD_CELL_VERTICAL_ALIGNMENT` se sobrar; (5) gerar v8 e comparar com o PDF; (6) code review.
