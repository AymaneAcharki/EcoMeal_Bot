@echo off
cd /d "%~dp0"
echo ================================
echo   EcoMeal Bot - Starting...
echo ================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

REM Check if LM Studio is running
curl -s http://localhost:1234/v1/models >nul 2>&1
if errorlevel 1 (
    echo WARNING: LM Studio not detected on port 1234
    echo Starting without LLM - using database recipes only
    echo.
)

REM Run Streamlit
echo Starting Streamlit on http://localhost:8501
echo.
python -m streamlit run app.py --server.port 8501

pause
