@echo off
echo Testing game...
echo.
echo 1. Checking game file...
dir "dist\planegame.exe"
echo.
echo 2. Running game for 5 seconds...
start "" "dist\planegame.exe"
timeout /t 5
taskkill /f /im "planegame.exe" 2>nul
echo.
echo Test completed.
echo Please tell me what you saw:
echo - Game window opened?
echo - Any error messages?
echo - Could you see login screen?
echo.
pause