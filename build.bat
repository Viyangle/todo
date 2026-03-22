@echo off
setlocal

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found: .venv\Scripts\python.exe
    echo Please create the virtual environment and install dependencies first.
    pause
    exit /b 1
)

echo [1/4] Using virtual environment...
".venv\Scripts\python.exe" -c "import sys; print(sys.executable)" || goto :fail

echo [2/4] Ensuring PyInstaller is installed...
".venv\Scripts\python.exe" -m pip install pyinstaller || goto :fail

echo [3/4] Cleaning old build output...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo [4/4] Building executable...
".venv\Scripts\python.exe" -m PyInstaller Todo.spec || goto :fail

echo.
echo Build completed successfully.
echo Output: dist\Todo\Todo.exe
pause
exit /b 0

:fail
echo.
echo Build failed.
pause
exit /b 1
