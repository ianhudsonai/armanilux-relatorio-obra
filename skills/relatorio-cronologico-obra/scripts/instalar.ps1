# Instalador do Relatório Cronológico de Obra (Armanilux).
# Fica dentro da skill, que é a pasta copiada para %USERPROFILE%\.codex\skills\.
# Pode rodar de novo: se Python, FFmpeg e as bibliotecas já existem, só confere.

$OutputEncoding = [System.Text.Encoding]::UTF8
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

function Escrever-Titulo($texto) { Write-Host $texto -ForegroundColor Cyan }
function Escrever-Ok($texto) { Write-Host $texto -ForegroundColor Green }
function Escrever-Aviso($texto) { Write-Host $texto -ForegroundColor Yellow }

Escrever-Titulo ""
Escrever-Titulo "Instalação do Relatório Cronológico de Obra (Armanilux)"
Escrever-Titulo ""
Write-Host "Se o Windows abrir uma janela perguntando se você permite alterações, clique em Sim."
Write-Host "Isso é o controle de conta (UAC). O instalador não aperta esse botão."
Write-Host "Se a janela não aparecer, a instalação segue sem administrador."
Write-Host ""

function Atualizar-Caminho {
    $maquina = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $usuario = [Environment]::GetEnvironmentVariable("Path", "User")
    $links = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links"
    $env:Path = "$maquina;$usuario;$links"
}

function Comando-Existe($nome) {
    return $null -ne (Get-Command $nome -ErrorAction SilentlyContinue)
}

function Acrescentar-CaminhoUsuario($diretorio) {
    if (-not $diretorio -or -not (Test-Path $diretorio)) { return }
    $atual = [Environment]::GetEnvironmentVariable("Path", "User")
    $partes = @()
    if ($atual) { $partes = $atual.Split(';') | Where-Object { $_ } }
    if ($partes -contains $diretorio) {
        Atualizar-Caminho
        return
    }
    $novo = if ($atual) { "$atual;$diretorio" } else { $diretorio }
    [Environment]::SetEnvironmentVariable("Path", $novo, "User")
    Atualizar-Caminho
}

function Winget-Instalar($id) {
    if (-not (Comando-Existe "winget")) {
        Write-Host "Não encontrei o winget. Na Microsoft Store, instale o 'Instalador de Aplicativo' e peça o relatório de novo."
        exit 1
    }
    Escrever-Aviso "Instalando $id para o seu usuário (sem administrador, quando o Windows permite)."
    & winget install --id $id -e --scope user --accept-package-agreements --accept-source-agreements
    $codigo = $LASTEXITCODE
    if ($codigo -eq 0 -or $codigo -eq -1978335189) {
        Atualizar-Caminho
        return
    }
    Escrever-Aviso "A instalação só para o usuário não concluiu. Se abrir a janela Sim ou Não, clique em Sim."
    & winget install --id $id -e --accept-package-agreements --accept-source-agreements
    $codigo = $LASTEXITCODE
    Atualizar-Caminho
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

function Achar-Ffmpeg {
    Atualizar-Caminho
    $comando = Get-Command ffmpeg -ErrorAction SilentlyContinue
    if ($comando) { return $comando.Source }
    $atalho = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links\ffmpeg.exe"
    if (Test-Path $atalho) { return $atalho }
    $pacotes = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
    if (Test-Path $pacotes) {
        $achado = Get-ChildItem -Path $pacotes -Filter ffmpeg.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($achado) { return $achado.FullName }
    }
    return $null
}

Atualizar-Caminho
$python = Achar-Python
if (-not (Python-Serve $python)) {
    Winget-Instalar "Python.Python.3.12"
    $python = Achar-Python
}
if (-not (Python-Serve $python)) {
    Write-Host "O Python 3.10 ou mais novo não ficou disponível depois da instalação."
    exit 1
}
Escrever-Ok "Python: $python"

if (-not (Achar-Ffmpeg)) {
    Winget-Instalar "Gyan.FFmpeg"
    if (-not (Achar-Ffmpeg)) {
        Winget-Instalar "FFmpeg.FFmpeg"
    }
}
$ffmpeg = Achar-Ffmpeg
if ($ffmpeg) {
    Acrescentar-CaminhoUsuario (Split-Path $ffmpeg -Parent)
    $ffmpeg = Achar-Ffmpeg
    Escrever-Ok "FFmpeg encontrado."
} else {
    Escrever-Aviso "O FFmpeg não ficou disponível. O Word ainda pode ser gerado; áudio e vídeo ficam sem transcrição."
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

$requisitos = Join-Path $PSScriptRoot "requirements.txt"
if (-not (Test-Path $requisitos)) {
    $raiz = Split-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) -Parent
    $requisitos = Join-Path $raiz "requirements.txt"
}
if (-not (Test-Path $requisitos)) {
    Write-Host "Não encontrei requirements.txt ao lado de instalar.ps1."
    exit 1
}
Escrever-Titulo "Instalando bibliotecas. Na primeira vez o modelo de voz é baixado para este computador..."
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r $requisitos
if ($LASTEXITCODE -ne 0) {
    Write-Host "A instalação das bibliotecas falhou. Confira a internet e peça o relatório de novo."
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

Atualizar-Caminho
Escrever-Ok ""
Escrever-Ok "Pronto."
Write-Host "PYTHON=$venvPython"
if ($ffmpeg) { Write-Host "FFMPEG=$ffmpeg" } else { Write-Host "FFMPEG=" }
Write-Host "Pasta das obras: $pasta"
Write-Host "O relatório pode continuar agora, sem reiniciar o computador."
exit 0
