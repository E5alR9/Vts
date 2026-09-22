@echo off
cd /d "%~dp0"
python "%~dp0auto_clicker_tool.py"
if errorlevel 1 pause
