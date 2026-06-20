@echo off
title Spectrum Anomaly Detection - Starting...
color 0A
cls

:: المسار الكامل لـ Python
set PYTHON=C:\Users\Admin\AppData\Local\Programs\Python\Python311\python.exe
set PIP=C:\Users\Admin\AppData\Local\Programs\Python\Python311\Scripts\pip.exe
set STREAMLIT=C:\Users\Admin\AppData\Local\Programs\Python\Python311\Scripts\streamlit.exe
set UVICORN=C:\Users\Admin\AppData\Local\Programs\Python\Python311\Scripts\uvicorn.exe

:: مسار المشروع
set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

echo.
echo  ==========================================
echo   Spectrum Anomaly Detection System
echo   ITC Egypt 2026
echo  ==========================================
echo.

:: ────────────────────────────────────────────
:: 1. فحص Python
:: ────────────────────────────────────────────
echo [1/5] Checking Python...
"%PYTHON%" --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found at %PYTHON%
    pause
    exit /b 1
)
echo        OK

:: ────────────────────────────────────────────
:: 2. تثبيت المتطلبات لو مش موجودة
:: ────────────────────────────────────────────
echo [2/5] Checking dependencies...
"%PYTHON%" -c "import fastapi, streamlit" >nul 2>&1
if errorlevel 1 (
    echo        Installing requirements, please wait...
    "%PIP%" install -r requirements.txt -q
    "%PIP%" install -r requirements-ml.txt -q
    echo        Done.
) else (
    echo        OK
)

:: ────────────────────────────────────────────
:: 3. تشغيل Ollama
:: ────────────────────────────────────────────
echo [3/5] Starting Ollama (AI Agent)...
tasklist /FI "IMAGENAME eq ollama.exe" 2>nul | find /I "ollama.exe" >nul
if errorlevel 1 (
    start /B "" ollama serve >logs\ollama.log 2>&1
    timeout /t 3 /nobreak >nul
    echo        Started.
) else (
    echo        Already running.
)

:: ────────────────────────────────────────────
:: 4. تشغيل FastAPI
:: ────────────────────────────────────────────
echo [4/5] Starting API server (FastAPI :8000)...
start "Spectrum API" /MIN cmd /c ""%UVICORN%" src.api.main:app --host 0.0.0.0 --port 8000 --reload > logs\api.log 2>&1"
timeout /t 3 /nobreak >nul
echo        Started.

:: ────────────────────────────────────────────
:: 5. تشغيل Streamlit
:: ────────────────────────────────────────────
echo [5/5] Starting Dashboard (Streamlit :8501)...
start "Spectrum Dashboard" /MIN cmd /c ""%STREAMLIT%" run src\dashboard\app.py --server.port 8501 --server.headless true > logs\dashboard.log 2>&1"
timeout /t 4 /nobreak >nul
echo        Started.

:: ────────────────────────────────────────────
:: فتح المتصفح
:: ────────────────────────────────────────────
echo.
echo  ==========================================
echo   All services running!
echo.
echo   Dashboard : http://localhost:8501
echo   API Docs  : http://localhost:8000/docs
echo   Ollama    : http://localhost:11434
echo  ==========================================
echo.
echo  Opening dashboard in browser...
timeout /t 2 /nobreak >nul
start http://localhost:8501

echo.
echo  Press any key to STOP all services...
pause >nul

:: ────────────────────────────────────────────
:: إيقاف كل حاجة
:: ────────────────────────────────────────────
echo.
echo  Stopping all services...
taskkill /FI "WINDOWTITLE eq Spectrum API*" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq Spectrum Dashboard*" /F >nul 2>&1
echo  Done. Goodbye!
timeout /t 2 /nobreak >nul
