@echo off
REM Run this AFTER installing Git and creating a new repo on GitHub.
REM Repo: https://github.com/ANUJ-codes07/Cosmic-SafeCli

echo Initializing Git...
git init
git add .
git commit -m "Initial commit: Cosmic SafeCLI for GitHub Copilot CLI Challenge"
git branch -M main

echo.
echo Add remote and push:
echo   git remote add origin https://github.com/ANUJ-codes07/Cosmic-SafeCli.git
echo   git push -u origin main
echo.
pause
