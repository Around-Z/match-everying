@echo off
setlocal enabledelayedexpansion

title Matching Platform Launcher

echo ========================================
echo   Multi-Scenario Matching Platform
echo ========================================
echo.

cd /d "%~dp0"

:: ── 1. Locate Python ──────────────────────────────────────────────
set "PYTHON="

:: 1a. Try the python/python3 in PATH
where python  >nul 2>&1 && for /f "delims=" %%p in ('where python  2^>nul') do if "!PYTHON!"=="" set "PYTHON=%%p"
where python3 >nul 2>&1 && for /f "delims=" %%p in ('where python3 2^>nul') do if "!PYTHON!"=="" set "PYTHON=%%p"

:: 1b. Scan common Anaconda locations (D: first — matches user setup)
if "!PYTHON!"=="" for %%d in (
    "D:\Users\AroundZ\anaconda3"
    "C:\Users\%USERNAME%\anaconda3"
    "D:\anaconda3"
    "C:\anaconda3"
    "C:\ProgramData\anaconda3"
    "%USERPROFILE%\anaconda3"
    "%LOCALAPPDATA%\Programs\Python\Python312"
    "%LOCALAPPDATA%\Programs\Python\Python311"
    "%LOCALAPPDATA%\Programs\Python\Python310"
    "%LOCALAPPDATA%\Microsoft\WindowsApps"
) do (
    if "!PYTHON!"=="" if exist "%%~d\python.exe"  set "PYTHON=%%~d\python.exe"
    if "!PYTHON!"=="" if exist "%%~d\python3.exe" set "PYTHON=%%~d\python3.exe"
)

if "!PYTHON!"=="" (
    echo [ERROR] Python not found.
    echo         Tried: PATH, common Anaconda/Python install locations.
    echo         Install Python or edit this script to set PYTHON manually.
    pause
    exit /b 1
)
echo [CHECK] Python: !PYTHON!
for /f "tokens=*" %%v in ('"!PYTHON!" --version 2^>^&1') do echo         %%v
echo.

:: ── 2. Check Docker daemon is running ─────────────────────────────
echo [0/3] Checking Docker...
docker info >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Docker daemon is not running or Docker is not installed.
    echo         Start Docker Desktop first, then re-run this script.
    pause
    exit /b 1
)
echo [OK]   Docker is running.
echo.

:: ── 3. Start Docker containers & wait for MySQL health ────────────
echo [1/3] Starting Docker containers...
docker compose -f "%~dp0docker-compose.yml" up -d
if !errorlevel! neq 0 (
    echo [ERROR] docker compose up failed. Check docker-compose.yml.
    pause
    exit /b 1
)

:: Poll MySQL healthcheck (up to 120 seconds)
echo [INFO] Waiting for MySQL to be ready...
set "MYSQL_READY=0"
for /l %%i in (1,1,60) do (
    docker inspect matching-mysql --format="{{.State.Health.Status}}" 2>nul | findstr /c:"healthy" >nul
    if !errorlevel! equ 0 (
        set "MYSQL_READY=1"
        goto :mysql_ok
    )
    :: Show progress dot every 4 seconds
    set /a "MOD=%%i %% 4"
    if !MOD! equ 0 <nul set /p "=."
    timeout /t 2 /nobreak >nul
)
:mysql_ok
echo.
if "!MYSQL_READY!"=="1" (
    echo [OK]   MySQL is healthy.
) else (
    echo [WARN] MySQL healthcheck timed out. Starting anyway...
    echo        If backend fails, run: docker compose ps
)
echo.

:: ── 4. Kill any process on port 8001 (exact match) ───────────────
echo [INFO] Checking port 8001...
set "FOUND_PID="
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /r /c:":8001[ ]" 2^>nul') do (
    set "FOUND_PID=%%a"
)
if not "!FOUND_PID!"=="" (
    echo [INFO] Port 8001 is occupied by PID !FOUND_PID! — killing...
    taskkill /PID !FOUND_PID! /F >nul 2>&1
    timeout /t 1 /nobreak >nul
    echo [OK]   Port 8001 freed.
) else (
    echo [OK]   Port 8001 is free.
)
echo.

:: ── 5. Start backend ──────────────────────────────────────────────
echo [2/3] Starting backend on port 8001...
start "Matching-Backend" cmd /k "title Matching-Backend && cd /d "%~dp0backend" && "!PYTHON!" run.py"

:: Poll backend health endpoint (up to 30 seconds)
echo [INFO] Waiting for backend...
set "BACKEND_OK=0"
for /l %%i in (1,1,15) do (
    curl -s -o nul -w "%%{http_code}" http://localhost:8001/api/health 2>nul | findstr "200" >nul
    if !errorlevel! equ 0 (
        set "BACKEND_OK=1"
        goto :backend_ok
    )
    timeout /t 2 /nobreak >nul
)
:backend_ok
if "!BACKEND_OK!"=="1" (
    echo [OK]   Backend is responding.
) else (
    echo [WARN] Backend health check timed out — it may still be starting.
    echo        Check the Matching-Backend window for errors.
)
echo.

:: ── 6. Check Node.js & node_modules ───────────────────────────────
where node >nul 2>&1
if !errorlevel! neq 0 (
    echo [ERROR] Node.js not found in PATH. Install Node.js ^>= 18 first.
    pause
    exit /b 1
)
if not exist "%~dp0frontend\node_modules" (
    echo [WARN] node_modules not found. Running npm install...
    cd /d "%~dp0frontend"
    call npm install
    if !errorlevel! neq 0 (
        echo [ERROR] npm install failed. Check the output above.
        cd /d "%~dp0"
        pause
        exit /b 1
    )
    cd /d "%~dp0"
    echo [OK]   Dependencies installed.
)
echo.

:: ── 7. Start frontend ─────────────────────────────────────────────
echo [3/3] Starting frontend on port 3000...
start "Matching-Frontend" cmd /k "title Matching-Frontend && cd /d "%~dp0frontend" && npm run dev"
echo [OK]   Frontend starting (Next.js dev server)...

:: ── 8. Summary ────────────────────────────────────────────────────
echo.
echo ========================================
echo   Backend  : http://localhost:8001
echo   Docs     : http://localhost:8001/docs
echo   Frontend : http://localhost:3000
echo ========================================
echo.
echo   Demo accounts:
echo     Admin     : admin@qm.com     / admin123
echo     Designer  : dsn@demo.com     / demo123456
echo     User      : xm@demo.com      / demo123456
echo.
echo   Close CMD windows to stop all services.
echo ========================================
echo.

pause
endlocal
