@echo off
rem Browser = Nengo GUI (press Play, bottom-right). A MuJoCo window opens and flies in sync.
call "%USERPROFILE%\AppData\Local\miniconda3\Scripts\activate.bat" hyperlif
cd /d "%~dp0.."
nengo_gui gui_y6_mujoco.py
pause
