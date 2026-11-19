@echo off
cd /d "%~dp0"
echo.
echo Armanilux - este atalho e opcional.
echo O jeito normal e colar no Codex as tres linhas do comeco do README.
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
