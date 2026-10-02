@echo off
rem Re-runs every offline result, figure, video and the deck (~12 min).
call "%USERPROFILE%\AppData\Local\miniconda3\Scripts\activate.bat" hyperlif
cd /d "%~dp0.."
python y6_mujoco_sim.py --validate
python y6_mujoco_sim.py --ctrl classical
python y6_mujoco_sim.py --ctrl nef_lif
python y6_mujoco_sim.py --ctrl classical --wind 4
python y6_mujoco_sim.py --ctrl nef_lif --wind 4
python y6_mujoco_sim.py --ctrl classical --wind 4 --integral
python y6_mujoco_sim.py --ctrl nef_lif --wind 4 --integral
python make_figures.py
python render_video.py results\classical.npz "Classical cascade PD (paper ctrl)"
python render_video.py results\nef_lif.npz "Spiking NEF (LIF) + neural allocator"
C:\Research\hover3dof\.venv\Scripts\python.exe deck\build_deck_y6.py
pause
