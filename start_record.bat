@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONUTF8=1
set MUJOCO_GL=glfw
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] .venv not found, see README first
    pause
    exit /b 1
)
echo === record video from best model ===
".venv\Scripts\python.exe" 07_tools\rec_video.py creep --steps 3000
pause
