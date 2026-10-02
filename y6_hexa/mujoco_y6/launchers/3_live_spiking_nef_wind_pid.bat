@echo off
call "%USERPROFILE%\AppData\Local\miniconda3\Scripts\activate.bat" hyperlif
cd /d "%~dp0.."
python run_realtime.py --ctrl nef_lif --wind 4 --integral %*
pause
