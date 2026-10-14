@echo off
setlocal
cd /d "%~dp0"
"C:\Program Files\Python314\python.exe" server.py
if errorlevel 1 pause
