@echo off
REM Hackathon demo — runs Cosmic SafeCLI with a dangerous command so you see the full flow.
REM Run this from the project root (folder that contains safe.py).
cd /d "%~dp0"
REM Uses a nonexistent path so nothing in your project can be deleted.
echo Running demo: python safe.py "rm -rf /nonexistent/cosmic-demo-safe"
echo.
python safe.py "rm -rf /nonexistent/cosmic-demo-safe"
echo.
pause
