# Atalho da raiz do repositório. A instalação de verdade está na skill de preparação.
$destino = Join-Path $PSScriptRoot "skills\preparar-projeto-armanilux\scripts\instalar.ps1"
if (-not (Test-Path $destino)) {
    Write-Host "Não encontrei o instalador em $destino"
    exit 1
}
& $destino @args
exit $LASTEXITCODE
