@echo off
cd /d "%~dp0"
echo.
echo Armanilux - Relatorio Cronologico de Obra
echo.
echo O Windows pode abrir uma janela pedindo permissao de administrador.
echo Isso e o UAC. Clique em Sim. Este instalador nao aperta esse botao.
echo Se nenhuma janela aparecer, a instalacao segue sozinha.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0instalar.ps1"
echo.
if errorlevel 1 (
  echo A instalacao terminou com erro. Leia as mensagens acima.
) else (
  echo Instalacao concluida.
)
echo.
pause
