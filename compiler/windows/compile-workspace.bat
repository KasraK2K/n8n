@echo off
powershell -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0compile-workspace.ps1"
pause