@echo off
rem resurrect.cmd - Windows cmd/PowerShell shim. Runs the bash `resurrect` beside
rem it via Git Bash, so there is ZERO logic here (single source of truth = resurrect).
setlocal
set "BASH=%ProgramFiles%\Git\bin\bash.exe"
if not exist "%BASH%" set "BASH=%ProgramW6432%\Git\bin\bash.exe"
if not exist "%BASH%" set "BASH=%LocalAppData%\Programs\Git\bin\bash.exe"
if not exist "%BASH%" (
    echo resurrect: Git Bash not found - run from Git Bash or WSL instead.1>&2
    exit /b 1
)
"%BASH%" "%~dp0resurrect" %*
