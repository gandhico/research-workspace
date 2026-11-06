# MuJoCo digital twin

The simulation half of the project: the canonical model, the simulated controllers and the
checks that tie the model to the real vehicle. The flight tools in `../flight` read the model
from here (the Lua mixer, the live twin view).

| Path | What |
|---|---|
| `omnidrone.xml` | Canonical model: 2.5 kg cube, eight rotor sites with full frames, motor actuators along each site's +Z. Mesh in `assets/` |
| `mjmodel.xml` | The same model as saved by MuJoCo (radians), used by `control/render_trace_gif.py` |
| `control/` | Geometric PD (`hover.py`), missions and campaigns (`missions.py`), Nengo controllers. Guides: `control/HOVER_GUIDE.md`, `control/MISSION_CAMPAIGN.md`. Results in `control/output/` |
| `physics/` | Parameters with their status (`omnicopter_parameters.json`) and identification measurements |
| `review/` | Model review and the rotor-frame check (`review/verify_rotor_frames.py`) |
| `validation/` | Common log schema, validation gates and the paired-log validator (twin versus hardware) |
| `docs/` | Methodology, the twin↔hardware validation protocol, controller validation, paper draft |
| `DATA_MANIFEST.csv` | Large files kept out of git |

Quick checks:

```
python -m mujoco.viewer --mjcf=omnidrone.xml
python review/verify_rotor_frames.py
python control/hover.py --headless --duration 5
```

The model is not yet identified against the real vehicle: thrust per rotor (10 N assumed),
mass and inertia, propeller reaction torque and motor lag are open. See
[`docs/DIGITAL_TWIN_METHODOLOGY.md`](docs/DIGITAL_TWIN_METHODOLOGY.md) and `../PROGRESS_LOG.md`.
