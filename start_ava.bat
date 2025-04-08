@echo off
echo Starting AVA Style Assistant...
echo.

echo Running uAgents Bureau - this will coordinate all agents...
echo (Web server, Stylist Agent, and Upcycler Agent)
start cmd /k "cd %~dp0 && python bureau.py"

echo.
echo AVA Style Assistant is now running!
echo Open http://localhost:8080 in your browser
echo.
echo Press any key to exit this window (agents will keep running)
pause > nul 