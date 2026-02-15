@echo off
REM Hackathon demo — runs Cosmic SafeCLI with a dangerous command so you see the full flow.
cd /d "%~dp0"
echo Running demo: python safe.py "rm -rf project"
echo.
python safe.py "rm -rf project"
echo.
pause
