@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

set "PY="
where pythonw >nul 2>nul && set "PY=pythonw"
if not defined PY where python >nul 2>nul && set "PY=python"

if not defined PY (
    echo Python 3.9+ не найден в PATH.
    echo Установите Python и повторите запуск.
    pause
    exit /b 1
)

if /i "%PY%"=="pythonw" (
    start "" pythonw "%~dp0lpp_ide.py"
) else (
    python "%~dp0lpp_ide.py"
    if errorlevel 1 pause
)
exit /b 0
