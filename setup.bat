@echo off
echo ========================================
echo   Futuristic Blog - Setup Script
echo ========================================
echo.

echo [1/4] Installing Backend Dependencies...
cd /d %~dp0backend
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install backend dependencies
    pause
    exit /b 1
)

echo.
echo [2/4] Installing Frontend Dependencies...
cd /d %~dp0frontend
npm install
if %errorlevel% neq 0 (
    echo Error: Failed to install frontend dependencies
    pause
    exit /b 1
)

echo.
echo [3/4] Creating MySQL Database...
echo Please make sure MySQL is running and create the database:
echo CREATE DATABASE futuristic_blog;
echo.

echo [4/4] Setup Complete!
echo.
echo ========================================
echo   Next Steps:
echo   1. Update backend/.env with your MySQL credentials
echo   2. Run start.bat to start the servers
echo ========================================
echo.
pause
