@echo off
title PAC Medical System - Desktop Launcher
color 0A

echo.
echo     ╔══════════════════════════════════════════════════════════╗
echo     ║               PAC MEDICAL SYSTEM                         ║
echo     ║            Desktop Application Launcher                  ║
echo     ║                                                          ║
echo     ║          🏥 Medical Image Management System              ║
echo     ║          🗄️  Database: Supabase PostgreSQL                ║
echo     ║          🌐 Full-Featured Desktop App                    ║
echo     ╚══════════════════════════════════════════════════════════╝
echo.

REM Check requirements
echo [1/4] Checking system requirements...
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Node.js not found
    echo Please install Node.js from: https://nodejs.org/
    echo.
    pause
    exit /b 1
) else (
    echo ✅ Node.js found
)

python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python not found
    echo Please install Python from: https://python.org/
    echo.
    pause
    exit /b 1
) else (
    echo ✅ Python found
)

echo.
echo [2/4] Installing dependencies (first run may take a few minutes)...

REM Install backend dependencies
pip install uvicorn fastapi psycopg2-binary python-jose passlib bcrypt python-multipart aiofiles pillow pydicom numpy aioredis python-dotenv >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Some Python packages may need manual installation
)

REM Install node dependencies
if not exist "node_modules" (
    echo Installing Node.js dependencies...
    npm install --silent >nul 2>&1
)

REM Install frontend dependencies  
if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    cd frontend
    npm install --legacy-peer-deps --silent >nul 2>&1
    cd ..
)

echo ✅ Dependencies ready
echo.

echo [3/4] Starting PAC Medical System...
echo      Backend API:  http://127.0.0.1:8001
echo      Frontend UI:  http://127.0.0.1:3000
echo      Database:     Supabase (Cloud)
echo.
echo [4/4] Launching application window...
echo.

REM Start the application
npm start

echo.
echo PAC Medical System has been closed.
echo Thank you for using PAC!
echo.
pause
