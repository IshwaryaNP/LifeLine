@echo off
echo ========================================================
echo   Starting Lifeline Triage Cyclone Response System
echo ========================================================
echo.

echo [1/2] Launching FastAPI Backend on http://127.0.0.1:8000 ...
start "Lifeline Backend (FastAPI)" cmd /k "cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/2] Launching Vite Frontend on http://localhost:5173 ...
start "Lifeline Frontend (Vite React)" cmd /k "cd frontend && npm run dev"

echo.
echo ========================================================
echo   Both services started in dedicated terminal windows!
echo   - Backend API Docs: http://127.0.0.1:8000/docs
echo   - Frontend UI:      http://localhost:5173
echo ========================================================
pause
