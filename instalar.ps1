# Instalador do Relatório Cronológico de Obra (Armanilux).
# Pode rodar de novo: se Python, FFmpeg e as bibliotecas já existem, só confere.

$OutputEncoding = [System.Text.Encoding]::UTF8
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

function Escrever-Titulo($texto) { Write-Host $texto -ForegroundColor Cyan }
function Escrever-Ok($texto) { Write-Host $texto -ForegroundColor Green }
function Escrever-Aviso($texto) { Write-Host $texto -ForegroundColor Yellow }

Escrever-Titulo ""
Escrever-Titulo "Instalação do Relatório Cronológico de Obra (Armanilux)"
Escrever-Titulo ""
Write-Host "Se o Windows abrir uma janela escura perguntando se você permite alterações,"
Write-Host "isso é o controle de conta (UAC). Clique em Sim."
Write-Host "O instalador não consegue clicar nesse botão por você."
Write-Host "Se a janela não aparecer, a instalação continua sem precisar de administrador."
Write-Host ""

function Atualizar-Caminho {
    $maquina = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $usuario = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = "$maquina;$usuario"
}

function Comando-Existe($nome) {
    return $null -ne (Get-Command $nome -ErrorAction SilentlyContinue)
}

function Winget-Instalar($id) {
    if (-not (Comando-Existe "winget")) {
        Write-Host "Não encontrei o winget. Instale o 'Instalador de Aplicativo' pela Microsoft Store e rode este arquivo de novo."
        exit 1
    }
    Escrever-Aviso "Instalando $id. Pode aparecer a janela de permissão do Windows."
    & winget install --id $id -e --scope user --accept-package-agreements --accept-source-agreements
    $codigo = $LASTEXITCODE
    if ($codigo -eq 0 -or $codigo -eq -1978335189) {
        return
    }
    Escrever-Aviso "Tentando de novo sem limitar à pasta do usuário. Se abrir o UAC, clique em Sim."
    & winget install --id $id -e --accept-package-agreements --accept-source-agreements
    $codigo = $LASTEXITCODE
    if ($codigo -ne 0 -and $codigo -ne -1978335189) {
        Write-Host "O winget não concluiu a instalação de $id (código $codigo)."
        exit 1
    }
}

function Achar-Python {
    Atualizar-Caminho
    $candidatos = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python312\python.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python313\python.exe")
    )
    foreach ($candidato in $candidatos) {
        if (Test-Path $candidato) { return $candidato }
    }
    if (Comando-Existe "py") {
        $saida = & py -3.12 -c "import sys; print(sys.executable)" 2>$null
        if ($LASTEXITCODE -eq 0 -and $saida) { return "$saida".Trim() }
        $saida = & py -3 -c "import sys; print(sys.executable)" 2>$null
        if ($LASTEXITCODE -eq 0 -and $saida) { return "$saida".Trim() }
    }
    if (Comando-Existe "python") {
        return (Get-Command python).Source
    }
    return $null
}

function Python-Serve($exe) {
    if (-not $exe) { return $false }
    $nota = & $exe -c "import sys; print(sys.version_info[0] * 100 + sys.version_info[1])" 2>$null
    if ($LASTEXITCODE -ne 0) { return $false }
    return ([int]"$nota".Trim()) -ge 310
}

$python = Achar-Python
if (-not (Python-Serve $python)) {
    Winget-Instalar "Python.Python.3.12"
    Atualizar-Caminho
    $python = Achar-Python
}
if (-not (Python-Serve $python)) {
    Write-Host "O Python 3.10 ou mais novo não ficou disponível. Feche e abra o computador, ou rode este arquivo de novo."
    exit 1
}
Escrever-Ok "Python: $python"

Atualizar-Caminho
if (-not (Comando-Existe "ffmpeg")) {
    Winget-Instalar "Gyan.FFmpeg"
    Atualizar-Caminho
    if (-not (Comando-Existe "ffmpeg")) {
        Winget-Instalar "FFmpeg.FFmpeg"
        Atualizar-Caminho
    }
}
if (Comando-Existe "ffmpeg") {
    Escrever-Ok "FFmpeg encontrado."
} else {
    Escrever-Aviso "O FFmpeg não ficou no caminho. O relatório em Word ainda pode ser gerado; vídeo e alguns áudios ficam sem transcrição até o FFmpeg instalar."
}

$venv = Join-Path $env:USERPROFILE ".armanilux-relatorio\venv"
$venvPython = Join-Path $venv "Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Escrever-Titulo "Criando o ambiente Python da Armanilux..."
    & $python -m venv $venv
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $venvPython)) {
        Write-Host "Não consegui criar o ambiente em $venv."
        exit 1
    }
} else {
    Escrever-Ok "Ambiente já existe: $venv"
}

$requisitos = Join-Path $PSScriptRoot "skills\relatorio-cronologico-obra\scripts\requirements.txt"
if (-not (Test-Path $requisitos)) {
    $requisitos = Join-Path $PSScriptRoot "requirements.txt"
}
Escrever-Titulo "Instalando bibliotecas (na primeira vez isso baixa o Whisper; depois fica neste computador)..."
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r $requisitos
if ($LASTEXITCODE -ne 0) {
    Write-Host "A instalação das bibliotecas falhou. Confira a internet e rode este arquivo de novo."
    exit 1
}

$pasta = Join-Path $env:USERPROFILE "Documents\Armanilux\Relatorios-de-Obra"
New-Item -ItemType Directory -Force -Path $pasta | Out-Null
$aviso = Join-Path $pasta "LEIA-ME.txt"
if (-not (Test-Path $aviso)) {
    @"
Pasta de relatórios de obra da Armanilux.

Cada obra ganha uma subpasta com cinco pastas:
01-conversas, 02-projetos-pdf, 03-midias, 04-transcricoes, 05-relatorios.

Coloque o zip do WhatsApp em Downloads ou aqui.
O relatório em Word aparece em 05-relatorios.
Nada é enviado para um serviço de transcrição na internet.
"@ | Set-Content -Path $aviso -Encoding UTF8
}

Escrever-Ok ""
Escrever-Ok "Pronto."
Write-Host "Pasta das obras: $pasta"
Write-Host "Python da skill: $venvPython"
Write-Host ""
Write-Host "Próximo passo:"
Write-Host "1. Abra o aplicativo ChatGPT (o aplicativo novo, não o site)."
Write-Host "2. Escolha Codex e, em seguida, Este computador."
Write-Host "3. Cole o link e a frase abaixo."
Write-Host ""
Write-Host "https://github.com/ianhudsonai/armanilux-relatorio-obra/tree/main/skills/relatorio-cronologico-obra"
Write-Host "Instale esta skill com o skill-installer"
Write-Host ""
exit 0
