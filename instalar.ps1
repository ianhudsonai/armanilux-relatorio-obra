# Atalho da raiz do repositório. A instalação de verdade está na skill.
$destino = Join-Path $PSScriptRoot "skills\relatorio-cronologico-obra\scripts\instalar.ps1"
if (-not (Test-Path $destino)) {
    Write-Host "Não encontrei o instalador da skill em $destino"
    exit 1
}
& $destino
exit $LASTEXITCODE
