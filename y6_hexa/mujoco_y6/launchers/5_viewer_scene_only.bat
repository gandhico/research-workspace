@echo off
rem Passive scene viewer (no controller): inspect geometry, cameras ([ and ]), actuators (right panel sliders).
call "%USERPROFILE%\AppData\Local\miniconda3\Scripts\activate.bat" hyperlif
cd /d "%~dp0.."
python -m mujoco.viewer --mjcf=y6_turbine_scene.xml
pause
