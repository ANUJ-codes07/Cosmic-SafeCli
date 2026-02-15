@echo off
echo [Setting up demo environment...]
if exist demo_project rmdir /S /Q demo_project
mkdir demo_project
echo "This is a dummy file" > demo_project\important_data.txt
echo [Demo environment ready: 'demo_project' created]
echo.
echo [Running Cosmic SafeCLI Demo]
echo.
python safe.py "rm -rf demo_project"
echo.
echo [Demo Complete]
pause
