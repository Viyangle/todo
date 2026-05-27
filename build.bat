@echo off
setlocal

cd /d "%~dp0"
set "APP_NAME=Todo"
set "BUILD_DIR=build"
set "DIST_DIR=dist"
set "APP_DIST_DIR=%DIST_DIR%\%APP_NAME%"
set "PORTABLE_DIR=%DIST_DIR%\%APP_NAME%-Portable"

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
if exist "%BUILD_DIR%" rmdir /s /q "%BUILD_DIR%"
if exist "%DIST_DIR%" rmdir /s /q "%DIST_DIR%"

echo [4/4] Building executable...
".venv\Scripts\python.exe" -m PyInstaller Todo.spec || goto :fail
if not exist "%APP_DIST_DIR%\Todo.exe" goto :fail

echo [5/5] Preparing portable package...
mkdir "%PORTABLE_DIR%" || goto :fail
xcopy "%APP_DIST_DIR%\*" "%PORTABLE_DIR%\" /E /I /Y >nul || goto :fail
if not exist "%PORTABLE_DIR%\data" mkdir "%PORTABLE_DIR%\data" || goto :fail

echo.
echo Build completed successfully.
echo Executable: %APP_DIST_DIR%\Todo.exe
echo Portable package: %PORTABLE_DIR%\
echo Portable data dir: %PORTABLE_DIR%\data\
pause
exit /b 0

:fail
echo.
echo Build failed.
pause
exit /b 1
