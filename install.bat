@echo off
chcp 65001 >nul
echo.
echo  ===================================
echo   DaVinci - AI Coding Agent
echo   Installing...
echo  ===================================
echo.

:: Install package
pip install -e .

:: Create global launcher
echo @echo off > "%USERPROFILE%\davinci.bat"
echo chcp 65001 ^>nul >> "%USERPROFILE%\davinci.bat"
echo python -m davinci.cli %%* >> "%USERPROFILE%\davinci.bat"

echo.
echo  [OK] DaVinci installed!
echo.
echo  Usage:
echo    davinci --init          # Initialize in current project
echo    davinci "Your task"     # Run a task
echo    davinci --status        # Check status
echo    davinci --models        # List models
echo.
echo  Add to PATH if needed:
echo    %USERPROFILE%
echo.
pause
