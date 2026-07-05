@echo off
chcp 65001 >nul
title DaVinci HUD
python -m davinci.hud
if errorlevel 1 (
    echo.
    echo  Trying with pythonw...
    start /B pythonw -m davinci.hud
)
