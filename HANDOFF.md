# HANDOFF — armanilux-relatorio-obra (2026-11-19)

## Estado atual
Duas skills na `main` (PRs #5 a #8 mergeados): `preparar-projeto-armanilux` (perguntas + instalação) e `relatorio-cronologico-obra` (zip do WhatsApp → Word). 46 testes passando, CI verde no Windows e no Ubuntu.
Já funciona: busca automática do zip (nome com acento e parênteses), registro por SHA-256 (pendente → em andamento → relatório gerado → concluído), PDFs em ~25 s, transcrição local de áudio e vídeo, não duplica arquivos ao reprocessar, candidatos por etapa, folhas de contato (12 miniaturas por folha), capa, quadro-resumo, cores da marca, anexo só com mídia citada, faixa "RASCUNHO NÃO REVISADO" até a revisão gravar `"revisado": true`.
Teste real feito com uma obra de ~595 MB (pasta em `Documents\Armanilux\Relatorios-de-Obra\`, FORA do repo). Último Word: v6, revisado à mão nesta sessão. Ninguém viu o Word renderizado ainda (este PC não tem Word nem LibreOffice).

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
1. Ian abrir o v6 no Word e dar retorno sobre a aparência; ajustar o que ele pedir.
2. Ler o nome do arquivo em "<Mídia oculta> arquivo.pdf" (45 casos na obra de teste) — `parse_whatsapp.py`.
3. Mensagem reencaminhada ("[dd/mm, hh:mm] Nome: …") usar a data e o autor originais (12 casos) — `parse_whatsapp.py`.
4. Tabela/gráfico de dias úteis menos vermelha: marcos nomeados em vez de toda data consecutiva — `analyze._intervalos`, `build_charts.py`.
5. Linhas das etapas coloridas como no PDF (salmão = reprocesso, amarelo = ocioso) e uma frase objetiva por evento.
6. Instalação: linha de colagem citando `$skill-installer` e as URLs `/tree/main/skills/<nome>` (README, AGENTS.md).
7. Transcrição com cache por arquivo (não refazer tudo), e rodar em segundo plano.
8. Textos automáticos genéricos em `analyze.py` (`_impacto`, `_produtividade`, `_comentarios_etapa`) ainda afirmam coisas; trocar por "dado não identificado" quando não houver revisão.

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
