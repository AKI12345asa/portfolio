@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Personal Works - Local Preview

echo.
echo   ============================================
echo    Personal Works  ^|  local preview
echo   ============================================
echo.

if not exist "node_modules" (
  echo   [1/2] First run: installing dependencies, please wait...
  call npm install --registry=https://registry.npmmirror.com
  if errorlevel 1 (
    echo.
    echo   Install failed. Check your network, then run: npm install
    echo.
    pause
    exit /b 1
  )
)

echo   [2/2] Starting dev server...
echo         Browser will open at http://localhost:4321
echo.
echo   To stop the server: press Ctrl+C in this window,
echo   or simply close this window.
echo.

start "" /b cmd /c "timeout /t 5 >nul & start http://localhost:4321"

call npm run dev

echo.
echo   Server stopped.
pause
