# Instalar as skills da Armanilux (instruções para o agente)

Você é o Codex ou o Claude Code, e a pessoa pediu para instalar estas skills neste computador. Faça agora, sem pedir mais nada além das aprovações do aplicativo. Fale com a pessoa em português simples.

São duas skills, na pasta `skills/` deste repositório: `preparar-projeto-armanilux` e `relatorio-cronologico-obra`.

Não instale Python, Node nem git: num computador novo eles ainda não existem, e o `$preparar-projeto-armanilux` instala o Python depois. Use só o PowerShell, que já vem no Windows.

## 1. Descubra o destino

Instale só no aplicativo em que você está rodando. Nunca nos dois. Não procure outros aplicativos no computador para decidir.

- Você é o Claude Code (no terminal ou no aplicativo Claude): `%USERPROFILE%\.claude\skills`
- Você é o Codex (no aplicativo ChatGPT, no aplicativo Codex ou no terminal): `%USERPROFILE%\.codex\skills`. É a pasta em que o `$skill-installer` grava e que o Codex do aplicativo ChatGPT no Windows carregou no teste de 20/11/2026. (A documentação nova do Codex também cita `%USERPROFILE%\.agents\skills`; não copie para as duas.)
- Se a pessoa pediu um aplicativo específico, instale só nele, mesmo que você seja o outro.
- Se não souber qual você é, pergunte uma vez: "Este chat é do Codex ou do Claude Code?"

No Linux e no Mac, as mesmas pastas ficam em `~/.claude/skills`, `~/.agents/skills` e `~/.codex/skills`.

## 2. Instale

No Windows, rode no PowerShell, com `$destino` do passo 1 (o exemplo é do Codex; no Claude Code, troque `.codex\skills` por `.claude\skills`):

```powershell
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ProgressPreference = "SilentlyContinue"
$destino = Join-Path $env:USERPROFILE ".codex\skills"
$zip = Join-Path $env:TEMP "armanilux-relatorio-obra.zip"
$tmp = Join-Path $env:TEMP "armanilux-relatorio-obra"
Invoke-WebRequest "https://github.com/ianhudsonai/armanilux-relatorio-obra/archive/refs/heads/main.zip" -OutFile $zip
Expand-Archive $zip -DestinationPath $tmp -Force
New-Item -ItemType Directory -Force $destino | Out-Null
foreach ($nome in "preparar-projeto-armanilux", "relatorio-cronologico-obra") {
  if (Test-Path (Join-Path $destino $nome)) { Write-Output "$nome já está instalada"; continue }
  Copy-Item (Join-Path $tmp "armanilux-relatorio-obra-main\skills\$nome") $destino -Recurse
}
Get-ChildItem $destino -Filter SKILL.md -Recurse -Depth 1 | Select-Object FullName
```

O comando usa a internet: se o aplicativo pedir aprovação, peça para a pessoa aprovar.

Se uma das duas já estava instalada, ela não é trocada. Só se a pessoa pedir para atualizar ou reinstalar: renomeie a pasta antiga para `<nome>.antiga` (não apague) e rode de novo.

## 3. Confira e avise

- A última linha do comando deve listar `preparar-projeto-armanilux\SKILL.md` e `relatorio-cronologico-obra\SKILL.md` dentro de `$destino`.
- Diga: "Pronto. As skills entram no próximo chat. Abra um chat novo, neste computador, e escreva `$preparar-projeto-armanilux`." Essa skill faz as perguntas e instala Python, FFmpeg e as bibliotecas. Depois, o relatório de cada obra é `$relatorio-cronologico-obra`.

## Se der errado

- Sem internet ou acesso bloqueado: peça para a pessoa aprovar o acesso à rede e rode de novo.
- `Expand-Archive` falhou: rode de novo (o download pode ter sido cortado). Não instale Python.
- No Codex, se `$preparar-projeto-armanilux` não aparecer num chat novo: mova as duas pastas de `%USERPROFILE%\.codex\skills` para `%USERPROFILE%\.agents\skills` e abra outro chat novo.
