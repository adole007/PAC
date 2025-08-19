@echo off
echo ========================================
echo    PAC Medical Image Management System
echo           Desktop Application
echo ========================================
echo.
echo Starting PAC System...
echo Database: Supabase (Online)
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH
    echo Please install Node.js from https://nodejs.org/
    echo.
    pause
    exit /b 1
)

REM Check if npm is installed
npm --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: npm is not installed or not in PATH
    echo Please install Node.js which includes npm
    echo.
    pause
    exit /b 1
)

REM Check if uvicorn is installed
uvicorn --version >nul 2>&1
if errorlevel 1 (
    echo Installing Python dependencies...
    pip install uvicorn fastapi psycopg2-binary python-jose passlib bcrypt python-multipart aiofiles pillow pydicom numpy aioredis python-dotenv
    echo.
)

REM Install Node.js dependencies if needed
if not exist "node_modules" (
    echo Installing Node.js dependencies...
    npm install
    echo.
)

REM Install frontend dependencies if needed
if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    cd frontend
    npm install --legacy-peer-deps
    cd ..
    echo.
)

echo All dependencies are ready!
echo.
echo Starting PAC Desktop Application...
echo.
echo This will:
echo - Start the Python FastAPI backend (port 8001)
echo - Start the React frontend (port 3000)
echo - Connect to Supabase PostgreSQL database
echo - Open the application window
echo.
echo The application will be available at:
echo Frontend: http://127.0.0.1:3000
echo Backend API: http://127.0.0.1:8001
echo.
echo Press Ctrl+C to stop the application
echo ========================================
echo.

REM Start the Electron app
npm start

echo.
echo PAC System has been stopped.
pause
