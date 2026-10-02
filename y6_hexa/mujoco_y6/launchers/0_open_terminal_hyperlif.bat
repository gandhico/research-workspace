@echo off
rem Opens a terminal in mujoco_y6 with the hyperlif conda env active (mujoco 3.11, nengo 4.1, nengo-gui).
call "%USERPROFILE%\AppData\Local\miniconda3\Scripts\activate.bat" hyperlif
cd /d "%~dp0.."
echo Env: hyperlif   Folder: %CD%
echo Try:  python run_realtime.py --ctrl nef_lif
cmd /k
