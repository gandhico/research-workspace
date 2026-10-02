# Nengo GUI + MuJoCo Control

Environment
```
$py = 'C:\Research\papers\ACC2027_Gate_Residual_Control\.venv\Scripts\python.exe'
$root = 'C:\Research\papers\ACC2027_Gate_Residual_Control\experiments\nengo_nef_replication_2026-08-29'
```

X2 Missions
```
& $py "$root\launch_gui.py" --platform x2 --mission hover     --mujoco-viewer neural --realtime --viewer-fps 30
& $py "$root\launch_gui.py" --platform x2 --mission roll      --mujoco-viewer neural --realtime --viewer-fps 30
& $py "$root\launch_gui.py" --platform x2 --mission full3     --mujoco-viewer neural --realtime --viewer-fps 30
& $py "$root\launch_gui.py" --platform x2 --mission hard45    --mujoco-viewer neural --realtime --viewer-fps 30
& $py "$root\launch_gui.py" --platform x2 --mission hardstep  --mujoco-viewer neural --realtime --viewer-fps 30
& $py "$root\launch_gui.py" --platform x2 --mission yaw360    --mujoco-viewer neural --realtime --viewer-fps 30
```

CF2 Missions
```
& $py "$root\launch_gui.py" --platform cf2-rotor --mission hover     --mujoco-viewer neural --realtime --viewer-fps 30
& $py "$root\launch_gui.py" --platform cf2-rotor --mission roll      --mujoco-viewer neural --realtime --viewer-fps 30
& $py "$root\launch_gui.py" --platform cf2-rotor --mission full3     --mujoco-viewer neural --realtime --viewer-fps 30
& $py "$root\launch_gui.py" --platform cf2-rotor --mission hard45    --mujoco-viewer neural --realtime --viewer-fps 30
& $py "$root\launch_gui.py" --platform cf2-rotor --mission hardstep  --mujoco-viewer neural --realtime --viewer-fps 30
& $py "$root\launch_gui.py" --platform cf2-rotor --mission yaw360    --mujoco-viewer neural --realtime --viewer-fps 30
```