@echo off
REM Build a standalone Windows executable.
REM
REM Usage:
REM   build.bat          -- build in dist\MetodoMurbach\
REM   build.bat --clean  -- clean rebuild

cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

echo ==> Building Metodo Murbach standalone executable...
python -m PyInstaller murbach.spec %*

echo.
echo ==> Build complete!
echo     Output: dist\MetodoMurbach\
echo.
echo     To run: dist\MetodoMurbach\MetodoMurbach.exe
