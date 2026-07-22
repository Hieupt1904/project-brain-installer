@echo off
REM Project Brain launcher for Windows.
python "%~dp0.ai\scripts\agentctl.py" %*
if errorlevel 1 exit /b %errorlevel%
