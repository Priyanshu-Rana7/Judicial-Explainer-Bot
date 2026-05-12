@echo off
title Judicial Explainer Bot Launcher (React Edition)
echo ⚖️  Judicial Explainer Bot Launcher
echo -----------------------------------

:: 1. Start Backend
echo [1/3] Starting FastAPI Backend...
start "Judicial Backend" cmd /k "python -m uvicorn main:app --reload"

:: 2. Check and Start React Frontend
echo [2/3] Preparing React Frontend...
cd frontend-react

if not exist node_modules (
    echo 📦 node_modules not found. Installing React dependencies...
    echo (This may take a minute on the first run)
    call npm install
)

echo [3/3] Launching React Dashboard...
echo 🚀 Project will open at http://localhost:3000
echo.
npm run dev

pause
