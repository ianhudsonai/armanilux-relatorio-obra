@echo off
cd /d "%~dp0"
echo.
echo Armanilux - este atalho e opcional.
echo O jeito normal e pedir o relatorio no Codex. Ele mesmo roda o instalador.
echo Se o Windows pedir permissao, clique em Sim.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0skills\relatorio-cronologico-obra\scripts\instalar.ps1"
echo.
if errorlevel 1 (
  echo A instalacao terminou com erro. Leia as mensagens acima.
  pause
  exit /b 1
)
echo Instalacao concluida. Pode continuar no Codex.
pause
exit /b 0
