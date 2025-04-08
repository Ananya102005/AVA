@echo off
echo Starting AVA Style Assistant...
echo.
echo This script will start the fetch.ai agents and web server.
echo.

REM Check if Python virtual environment exists
if not exist fetch_env (
    echo Creating Python virtual environment...
    python -m venv fetch_env
    call fetch_env\Scripts\activate
    echo Installing Python dependencies...
    pip install -r requirements.txt
) else (
    echo Using existing virtual environment.
    call fetch_env\Scripts\activate
)

REM Check if Node.js dependencies are installed
if not exist node_modules (
    echo Installing Node.js dependencies...
    npm install
) else (
    echo Using existing Node.js dependencies.
)

REM Check if .env file exists
if not exist .env (
    echo Creating .env file...
    echo # Google Gemini API Key> .env
    echo GOOGLE_API_KEY=your-api-key-here>> .env
    echo.>> .env
    echo # Agent ports>> .env
    echo BODY_SCANNER_PORT=8002>> .env
    echo UPCYCLER_PORT=5000>> .env
    echo STYLIST_PORT=6000>> .env
    echo TREND_PORT=7000>> .env
    echo WEB_SERVER_PORT=3000>> .env
    echo.
    echo Please set your GOOGLE_API_KEY in the .env file.
) else (
    echo Using environment variables from .env file.
    echo Make sure you've set your GOOGLE_API_KEY in the .env file.
)

REM Start fetch.ai agents and web server
echo.
echo Starting agents with Gemini AI integration...
start "Body Scanner Agent" cmd /c "call fetch_env\Scripts\activate && python agents\simplified_server.py"
start "Upcycler Agent" cmd /c "call fetch_env\Scripts\activate && python agents\upcycler_server.py"
start "Stylist Agent" cmd /c "call fetch_env\Scripts\activate && python stylist_server.py"
start "Trend Agent" cmd /c "call fetch_env\Scripts\activate && python trend_server.py"

echo Waiting for agents to initialize (15 seconds)...
set /a wait_time=15
:wait_loop
if %wait_time% leq 0 goto continue
echo Waiting for  %wait_time% seconds, press CTRL+C to quit ...
timeout /t 1 > nul
set /a wait_time-=1
goto wait_loop

:continue
echo Starting web server...
echo.
echo When everything is running:
echo - Body Scanner Agent: http://localhost:8002
echo - Upcycler Agent: http://localhost:5000
echo - Stylist Agent: http://localhost:6000
echo - Trend Agent: http://localhost:7000
echo - Main Web Interface: http://localhost:3000
echo.
echo ---------------------------------------------------------------
echo AVA Style Assistant - Fetch.ai Agent Implementation with Gemini AI
echo This application uses fetch.ai agents with Gemini AI for style analysis
echo ---------------------------------------------------------------

node server.js 