# Omnicopter (Omnidrone): start here

An eight-rotor omnidirectional drone: rotors on the eight corners of a cube frame, reversible
(DShot-3D) motors, a Cube Orange+ running ArduPilot 4.7.1 with the 6DoF frame, and OptiTrack for
position. A MuJoCo digital twin supplies the mixer and is used to choose gains and to explain
what the real vehicle does.

**Current goal:** the first tethered hover. ArduPilot runs the 6DoF control onboard; a Python
ground station on the lab PC commands it in GUIDED mode. No Mission Planner and no RC.

## Folder map

```
omnicopter/
├── README.md             this page
├── PROGRESS_LOG.md       what was done and learned, day by day
├── requirements.txt      Python packages for both halves
├── flight/               the real vehicle
│   ├── HOVER_PLAN.md     status and next steps to the first hover  ← read before every lab day
│   ├── README.md         full guide: Cube set-up, OptiTrack, identification, gains
│   ├── RUNBOOK.md        click-by-click bench steps (older, written for Mission Planner)
│   ├── omni_gcs.py       ground-station window (uses gcs_core.py and twin_view.py)
│   ├── analyze_flight.py report and plots for one session; --archive stores the logs for git
│   ├── motor_test_6dof.py  motor map, spin direction and thrust direction, one motor at a time
│   ├── make_6dof_mixer.py  twin → ArduPilot Lua mixer (output in generated/)
│   ├── ap_link.py, ap_param_load.py, ap_param_audit.py, board_orientation.py   Cube link and parameters
│   ├── config/           parameter files written to the Cube (stages 1–5)
│   ├── generated/        the Lua mixer (copy to the Cube SD card, APM/scripts) and its JSON
│   ├── mocap/            OptiTrack bridge, room calibration, Motive rigid-body file
│   ├── tests/            offline tests against a fake Cube and a fake Motive
│   ├── data/             logs/ (every session), audits/ (Cube parameters, motor tests), reports/ (plots)
│   └── legacy/           the first serial, Pico W and motor scripts, kept for reference
└── twin/                 the MuJoCo digital twin
    ├── omnidrone.xml     canonical model (mesh in assets/)
    ├── control/          simulated controllers, missions and campaigns (results in control/output/)
    ├── physics/          physical parameters and identification
    ├── review/           model checks (rotor frames, model review)
    ├── validation/       twin-versus-hardware log comparison
    └── docs/             methodology, validation protocol, paper draft
```

## The cycle until the first hover

```
 1. check the hardware      props, rotor map, centre of mass         flight/HOVER_PLAN.md
 2. test strapped down      motor_test_6dof.py --props-on, step E    flight/HOVER_PLAN.md
 3. fly tethered            omni_gcs.py                              flight/HOVER_PLAN.md §4
 4. analyse                 analyze_flight.py --png                  flight/data/reports/
 5. explain with the twin   twin/omnidrone.xml, mixer JSON           PROGRESS_LOG.md
 6. fix and save            hardware, twin or gains; --archive; commit and push
```

The full workflow with plots and the rotor record sheet:
[Omnidrone workflow document](https://claude.ai/artifact/XFicFSkqcDCzY15TcdTRod).

## Set up on another computer

1. **Get the code.** If the repository is already cloned there (for example in `C:\Research`):

   ```
   git fetch origin
   git switch feature/system-identification
   git pull
   ```

   The project moved from `omnicopter/mujoco/` to `omnicopter/twin/` and `omnicopter/flight/` on
   2026-11-05. If an old `omnicopter/mujoco/` folder is still there after the switch, it holds
   only files git never tracked (virtual environments, workspace files, caches): move what you
   need into `twin/` and delete the rest.

   For a fresh clone of only this project:

   ```
   git clone --filter=blob:none --sparse https://github.com/gandhico/research-workspace.git
   cd research-workspace
   git sparse-checkout set omnicopter
   git switch feature/system-identification
   ```

2. **Python 3.11** with `python -m pip install -r omnicopter/requirements.txt`.

3. **Analyse without hardware.** All flight sessions are in `flight/data/logs` (compressed):

   ```
   cd omnicopter/flight
   python analyze_flight.py --list
   python analyze_flight.py 20261105_142801 --png
   ```

4. **Look at the twin:** `python -m mujoco.viewer --mjcf=omnicopter/twin/omnidrone.xml`.

5. **Run the offline tests:** `python flight/tests/test_gcs_core.py` (and the other `tests/test_*.py`).

The lab PC also needs Motive (NatNet on 192.168.2.2, unicast) and the Pico W Wi-Fi link to the
Cube; see `flight/HOVER_PLAN.md` §3.

## Rules

- **Never delete flight data.** The ground station writes `flight/data/logs/*.csv` (not in git).
  After a lab day run `python analyze_flight.py --archive`: it adds a compressed copy
  (`*.csv.gz`) of every new session, and those copies are committed.
- One branch for this phase: `feature/system-identification`. Commit and push at the end of each
  lab day, with a short entry in `PROGRESS_LOG.md`.
- Props on, vehicle tethered or strapped, a person on the physical battery kill. See the flight
  card in `flight/HOVER_PLAN.md`.
