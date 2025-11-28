@echo off
REM 5G Network Slice Traffic Generator - Windows One-Click Setup
REM Save as: setup.bat and run it

setlocal enabledelayedexpansion

echo.
echo ========================================
echo 5G Network Slice Generator - Setup
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Install Python 3.8+
    pause
    exit /b 1
)

echo [OK] Python found

REM Create directories
echo Creating directories...
if not exist backend mkdir backend
if not exist scheduler mkdir scheduler
if not exist slices\embb mkdir slices\embb
if not exist slices\urllc mkdir slices\urllc
if not exist slices\mmtc mkdir slices\mmtc
if not exist frontend mkdir frontend
echo [OK] Directories created

REM Setup Backend
echo.
echo ========================================
echo Setting up BACKEND (Port 8000)
echo ========================================
cd backend
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
echo Activating venv and installing requirements...
call venv\Scripts\activate.bat
pip install --upgrade pip >nul 2>&1
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 pydantic==2.5.0 python-multipart==0.0.6 websockets==12.0 aiohttp==3.9.0 numpy==1.24.3 python-dotenv==1.0.0 >nul 2>&1
call venv\Scripts\deactivate.bat
cd ..
echo [OK] Backend ready

REM Setup Scheduler
echo.
echo ========================================
echo Setting up SCHEDULER (Port 8001)
echo ========================================
cd scheduler
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
echo Activating venv and installing requirements...
call venv\Scripts\activate.bat
pip install --upgrade pip >nul 2>&1
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 pydantic==2.5.0 python-multipart==0.0.6 websockets==12.0 aiohttp==3.9.0 numpy==1.24.3 python-dotenv==1.0.0 >nul 2>&1
call venv\Scripts\deactivate.bat
cd ..
echo [OK] Scheduler ready

REM Setup eMBB
echo.
echo ========================================
echo Setting up eMBB SLICE (Port 8101)
echo ========================================
cd slices\embb
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
echo Activating venv and installing requirements...
call venv\Scripts\activate.bat
pip install --upgrade pip >nul 2>&1
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 pydantic==2.5.0 python-multipart==0.0.6 websockets==12.0 aiohttp==3.9.0 numpy==1.24.3 python-dotenv==1.0.0 >nul 2>&1
call venv\Scripts\deactivate.bat
cd ..\..
echo [OK] eMBB Slice ready

REM Setup URLLC
echo.
echo ========================================
echo Setting up URLLC SLICE (Port 8102)
echo ========================================
cd slices\urllc
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
echo Activating venv and installing requirements...
call venv\Scripts\activate.bat
pip install --upgrade pip >nul 2>&1
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 pydantic==2.5.0 python-multipart==0.0.6 websockets==12.0 aiohttp==3.9.0 numpy==1.24.3 python-dotenv==1.0.0 >nul 2>&1
call venv\Scripts\deactivate.bat
cd ..\..
echo [OK] URLLC Slice ready

REM Setup mMTC
echo.
echo ========================================
echo Setting up mMTC SLICE (Port 8103)
echo ========================================
cd slices\mmtc
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
echo Activating venv and installing requirements...
call venv\Scripts\activate.bat
pip install --upgrade pip >nul 2>&1
pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 pydantic==2.5.0 python-multipart==0.0.6 websockets==12.0 aiohttp==3.9.0 numpy==1.24.3 python-dotenv==1.0.0 >nul 2>&1
call venv\Scripts\deactivate.bat
cd ..\..
echo [OK] mMTC Slice ready

REM Setup Frontend
echo.
echo ========================================
echo Setting up FRONTEND (Port 3000)
echo ========================================
cd frontend

if not exist package.json (
    echo Initializing Next.js...
    call npx create-next-app@latest . --typescript --tailwind --no-eslint --skip-git ^
        --import-alias "@/*" >nul 2>&1
)

if not exist node_modules (
    echo Installing npm packages...
    call npm install >nul 2>&1
)
cd ..
echo [OK] Frontend ready

REM Create run script
echo.
echo Creating startup script...

(
echo @echo off
echo title 5G Network Slice Generator - Services
echo.
echo echo Starting all services...
echo echo.
echo.
echo echo [1/6] Starting Backend (8000)...
echo start "Backend (8000)" cmd /k "cd backend && venv\Scripts\activate && python app.py"
echo timeout /t 2 /nobreak >nul
echo.
echo echo [2/6] Starting Scheduler (8001)...
echo start "Scheduler (8001)" cmd /k "cd scheduler && venv\Scripts\activate && python generator.py"
echo timeout /t 2 /nobreak >nul
echo.
echo echo [3/6] Starting eMBB (8101)...
echo start "eMBB Slice (8101)" cmd /k "cd slices\embb && venv\Scripts\activate && python main.py"
echo timeout /t 2 /nobreak >nul
echo.
echo echo [4/6] Starting URLLC (8102)...
echo start "URLLC Slice (8102)" cmd /k "cd slices\urllc && venv\Scripts\activate && python main.py"
echo timeout /t 2 /nobreak >nul
echo.
echo echo [5/6] Starting mMTC (8103)...
echo start "mMTC Slice (8103)" cmd /k "cd slices\mmtc && venv\Scripts\activate && python main.py"
echo timeout /t 2 /nobreak >nul
echo.
echo echo [6/6] Starting Frontend (3000)...
echo start "Frontend (3000)" cmd /k "cd frontend && npm run dev"
echo.
echo echo.
echo echo ========================================
echo echo All services started!
echo echo ========================================
echo echo.
echo echo Backend:  http://localhost:8000
echo echo Scheduler: http://localhost:8001
echo echo eMBB:     http://localhost:8101
echo echo URLLC:    http://localhost:8102
echo echo mMTC:     http://localhost:8103
echo echo.
echo echo FRONTEND: http://localhost:3000
echo echo.
echo echo Close this window to continue...
echo pause
) > run_all.bat

echo [OK] Startup script created (run_all.bat)

REM Done
echo.
echo ========================================
echo SETUP COMPLETE!
echo ========================================
echo.
echo Next steps:
echo.
echo 1. Double-click run_all.bat to start all services
echo.
echo 2. Open browser: http://localhost:3000
echo.
echo 3. Configure simulation and click START
echo.
echo ========================================
echo.
pause