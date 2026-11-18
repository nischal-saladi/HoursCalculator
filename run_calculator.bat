@echo off
title Payroll Time Calculator
cd /d "%~dp0"
python time_calculator.py
if errorlevel 1 (
    echo.
    echo An error occurred running the time calculator.
    pause
)
