@echo off
cd /d "%~dp0"
echo.
echo Armanilux - este atalho e opcional.
echo O jeito normal e colar o link do repositorio no Codex ou no Claude Code e escrever: instale aqui.
echo Se o Windows pedir permissao, clique em Sim.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0skills\preparar-projeto-armanilux\scripts\instalar.ps1"
echo.
if errorlevel 1 (
  echo A instalacao terminou com erro. Leia as mensagens acima.
  pause
  exit /b 1
)
echo Instalacao concluida.
pause
exit /b 0
