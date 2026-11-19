# Instalar as skills da Armanilux

A pessoa cola uma linha só:

```text
https://github.com/ianhudsonai/armanilux-relatorio-obra instale as skills
```

Faça as duas skills. Fale com ela em português.

Repositório: `https://github.com/ianhudsonai/armanilux-relatorio-obra`

Skills:

- `skills/preparar-projeto-armanilux`
- `skills/relatorio-cronologico-obra`

## O que o instalador de skills aceita

Conferido no script `install-skill-from-github.py` do `$skill-installer` (openai/skills, pasta `skills/.system/skill-installer/scripts`, branch main):

- Um endereço só com `https://github.com/dono/repo`, sem caminho interno, faz o script parar com `Missing --path for GitHub URL.` Ele não descobre sozinho a pasta `skills/`.
- `--path` aceita vários caminhos na mesma execução. O nome da skill é o nome da pasta.
- Para listar antes: `list-skills.py --repo ianhudsonai/armanilux-relatorio-obra --path skills`
- Se a pasta de destino já existir, essa skill não é reinstalada. Apague a pasta antiga ou use outro destino só se a pessoa pedir para reinstalar.

O jeito mais seguro é uma execução só, com os dois caminhos:

```text
python install-skill-from-github.py --repo ianhudsonai/armanilux-relatorio-obra --path skills/preparar-projeto-armanilux skills/relatorio-cronologico-obra
```

O `python` e o script são os do `$skill-installer` já instalado no Codex. O script pede rede. Se o modo local pedir aprovação, peça para a pessoa aprovar.

Destino no Windows: `%USERPROFILE%\.codex\skills\`. No Linux e no Mac: `~/.codex/skills`.

## Se o $skill-installer não estiver disponível

Baixe o zip do repositório e copie as duas pastas para `%USERPROFILE%\.codex\skills\`.

Se existir a pasta `%USERPROFILE%\.claude` ou o comando `claude`, copie as mesmas duas pastas também para `%USERPROFILE%\.claude\skills\` (no Mac ou Linux, `~/.claude/skills`). Não copie para o Claude se nenhum dos dois existir.

## Depois de instalar

Diga que as skills entram no próximo chat. Peça para abrir um chat novo, neste computador, e escrever:

```text
$preparar-projeto-armanilux
```

Essa skill faz as perguntas e instala Python, FFmpeg e as bibliotecas. O relatório de cada obra, depois disso, é `$relatorio-cronologico-obra`.
