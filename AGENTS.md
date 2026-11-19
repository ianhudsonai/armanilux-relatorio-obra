# Instalar as skills da Armanilux

A pessoa cola isto:

```text
$skill-installer instale estas skills:
https://github.com/ianhudsonai/armanilux-relatorio-obra/tree/main/skills/preparar-projeto-armanilux
https://github.com/ianhudsonai/armanilux-relatorio-obra/tree/main/skills/relatorio-cronologico-obra
Se este computador não tiver Python, não instale Python: baixe o zip do repositório com PowerShell e copie as duas pastas para a pasta de skills deste aplicativo.
```

Versões antigas do README mandavam colar só `https://github.com/ianhudsonai/armanilux-relatorio-obra instale as skills`. Se vier assim, faça o mesmo.

Faça as duas skills. Fale com ela em português.

Repositório: `https://github.com/ianhudsonai/armanilux-relatorio-obra`

Skills:

- `skills/preparar-projeto-armanilux`
- `skills/relatorio-cronologico-obra`

## O que o instalador de skills aceita

Conferido no script `install-skill-from-github.py` do `$skill-installer` (openai/skills, pasta `skills/.system/skill-installer/scripts`, branch main):

- Um endereço só com `https://github.com/dono/repo`, sem caminho interno, faz o script parar com `Missing --path for GitHub URL.` Ele não descobre sozinho a pasta `skills/`.
- `--url` com `/tree/main/skills/<nome>` instala uma skill por execução. Com os dois endereços da linha de colagem, rode uma vez para cada um, ou use o comando abaixo.
- `--path` aceita vários caminhos na mesma execução. O nome da skill é o nome da pasta.
- Para listar antes: `list-skills.py --repo ianhudsonai/armanilux-relatorio-obra --path skills`
- Se a pasta de destino já existir, essa skill não é reinstalada. Apague a pasta antiga ou use outro destino só se a pessoa pedir para reinstalar.

O jeito mais seguro é uma execução só, com os dois caminhos:

```text
python install-skill-from-github.py --repo ianhudsonai/armanilux-relatorio-obra --path skills/preparar-projeto-armanilux skills/relatorio-cronologico-obra
```

O script pede rede. Se o aplicativo pedir aprovação, peça para a pessoa aprovar.

## Onde instalar

Instale só na pasta de skills do aplicativo que está executando estas instruções. Não instale em outro aplicativo. Não procure outras ferramentas no computador para decidir o destino. A existência de uma pasta ou de um comando de outro aplicativo não muda o destino.

- Se você é o Codex: `%USERPROFILE%\.codex\skills\` no Windows, `~/.codex/skills` no Linux e no Mac. Use o `$skill-installer` com o comando acima. O destino padrão dele já é essa pasta.
- Se você é o Claude Code: `~/.claude/skills` (no Windows, `%USERPROFILE%\.claude\skills`). Não use o instalador do Codex. Copie as duas pastas só para essa pasta do Claude Code.
- Se a pessoa pedir um aplicativo específico, instale só nele, mesmo que você seja outro aplicativo.

Não copie para os dois.

## Se o instalador do seu aplicativo não estiver disponível

Num computador novo isso é o normal: o `$skill-installer` é um script Python, e o Python só é instalado depois, pelo `$preparar-projeto-armanilux`. Não instale Python para isso. Baixe o zip do repositório com PowerShell e copie as duas pastas somente para a pasta de skills do aplicativo em que você está, como na lista acima.

No Codex, no Windows:

```powershell
$zip = Join-Path $env:TEMP "armanilux-relatorio-obra.zip"
$tmp = Join-Path $env:TEMP "armanilux-relatorio-obra"
Invoke-WebRequest "https://github.com/ianhudsonai/armanilux-relatorio-obra/archive/refs/heads/main.zip" -OutFile $zip
Expand-Archive $zip -DestinationPath $tmp -Force
$destino = Join-Path $env:USERPROFILE ".codex\skills"
New-Item -ItemType Directory -Force $destino | Out-Null
foreach ($nome in "preparar-projeto-armanilux", "relatorio-cronologico-obra") {
  if (Test-Path (Join-Path $destino $nome)) { Write-Output "$nome já está instalada"; continue }
  Copy-Item (Join-Path $tmp "armanilux-relatorio-obra-main\skills\$nome") $destino -Recurse
}
```

No Claude Code, troque `.codex\skills` por `.claude\skills`. Se a pasta da skill já existir, ela não é trocada; só apague ou substitua se a pessoa pedir para reinstalar.

## Depois de instalar

Diga que as skills entram no próximo chat. Peça para abrir um chat novo, neste computador, e escrever:

```text
$preparar-projeto-armanilux
```

Essa skill faz as perguntas e instala Python, FFmpeg e as bibliotecas. O relatório de cada obra, depois disso, é `$relatorio-cronologico-obra`.
