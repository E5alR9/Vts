@echo off
chcp 65001 >nul
cd /d "%~dp0"
python record_clean_dad_voiceprint.py
pause
