# analise.json

O arquivo fica em `04-transcricoes/analise.json`. O Word é montado a partir dele.

Campos que o script recalcula com `--recalcular`: `intervalos`, `kpis`, `etapas`, `gargalos`, `responsabilidades`, `recomendacoes`, `conclusao`, `produtividade`.

Campos que a revisão humana preenche e o script preserva:

- `observacoes_visuais`: lista de `{ "arquivo", "observacao" }`
- `comentarios`: por letra de etapa, textos que substituem Intervalos relevantes, Situação, Ponto crítico, Gargalo, Avaliação e Conclusão da etapa
- `recomendacoes_personalizadas`: lista de frases
- `conclusao_personalizada`: texto único
- `ajustes_eventos`: lista opcional aplicada numa nova leitura do zip. Cada item pode trazer `data`, `hora`, `autor`, `etapa_original`, `etapa`, `ocorrencia`, `impacto`

`eventos` é a lista cronológica. `etapa` é uma letra de A, B, C, D, E, F, G, H, I, J ou L. `pendencias` usa `status` igual a `Pendente` só para item que o grupo deixou aberto.

Datas internas estão em `AAAA-MM-DD`. O Word mostra `DD/MM/AAAA`. Não edite o número de dias úteis à mão: rode `--recalcular`.

Não grave este JSON de obra real no repositório público.
