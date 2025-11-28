@echo off
REM 5G Network Slice Traffic Generator - Start All Services
REM Double-click this file to start everything

title 5G Network Slice Generator - Dashboard
color 0A

echo.
echo ========================================
echo 5G Network Slice Traffic Generator
echo ========================================
echo.
echo Starting all services in separate windows...
echo.

REM Get the directory where this script is located
setlocal enabledelayedexpansion
set "BASE_DIR=%~dp0"

REM Start Backend (Port 8000)
echo [1/6] Starting Backend (Port 8000)...
start "Backend (8000)" cmd /k "cd /d !BASE_DIR!backend && venv\Scripts\activate.bat && python app.py"
timeout /t 2 /nobreak >nul

REM Start Scheduler (Port 8001)
echo [2/6] Starting Scheduler (Port 8001)...
start "Scheduler (8001)" cmd /k "cd /d !BASE_DIR!scheduler && venv\Scripts\activate.bat && python generator.py"
timeout /t 2 /nobreak >nul

REM Start eMBB Slice (Port 8101)
echo [3/6] Starting eMBB Slice (Port 8101)...
start "eMBB Slice (8101)" cmd /k "cd /d !BASE_DIR!slices\embb && venv\Scripts\activate.bat && python main.py"
timeout /t 2 /nobreak >nul

REM Start URLLC Slice (Port 8102)
echo [4/6] Starting URLLC Slice (Port 8102)...
start "URLLC Slice (8102)" cmd /k "cd /d !BASE_DIR!slices\urllc && venv\Scripts\activate.bat && python main.py"
timeout /t 2 /nobreak >nul

REM Start mMTC Slice (Port 8103)
echo [5/6] Starting mMTC Slice (Port 8103)...
start "mMTC Slice (8103)" cmd /k "cd /d !BASE_DIR!slices\mmtc && venv\Scripts\activate.bat && python main.py"
timeout /t 2 /nobreak >nul

REM Start Frontend (Port 3000)
echo [6/6] Starting Frontend (Port 3000)...
start "Frontend (3000)" cmd /k "cd /d !BASE_DIR!frontend && npm run dev"
timeout /t 3 /nobreak >nul

REM Show status
echo.
echo ========================================
echo ✓ All services started!
echo ========================================
echo.
echo Services Running:
echo.
echo   Backend........http://localhost:8000
echo   Scheduler......http://localhost:8001
echo   eMBB Slice....http://localhost:8101
echo   URLLC Slice...http://localhost:8102
echo   mMTC Slice....http://localhost:8103
echo.
echo   FRONTEND.....http://localhost:3000  ◄ OPEN THIS!
echo.
echo ========================================
echo.
echo Waiting for services to initialize...
timeout /t 5 /nobreak >nul

REM Try to open frontend in browser
echo Opening frontend in browser...
start http://localhost:3000

echo.
echo ========================================
echo SETUP COMPLETE!
echo ========================================
echo.
echo Your 5G Network Slice simulator is ready!
echo.
echo Keep this window open. Close it to stop monitoring.
echo.
pause