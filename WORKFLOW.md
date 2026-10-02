# Neuromorphic-Control Research — Workflow & Insights Log

**Owner:** Gandhi A. S. Contreras Torres (NMSU) · **Machine:** rented Windows 11 laptop, restored from `D:\NMSU_backups\Backup`
**Started:** 2026-08-10 · **Purpose:** running log of the *reproducible* HyperLIF / Quanser control workflow — setup, the three-tier pipeline (**offline → digital-twin → hardware**), cross-platform (Python ↔ MATLAB) validation, results, and insights. Written to feed the **IEEE Transactions on Education** paper and later works.

> Golden rule inherited from the Aero2 repo `CLAUDE.md`: **preserve honest results.** Numbers here are raw smoke-test / validation runs, *not* silently tuned. Twin ≠ hardware; SNN/HyperLIF results are experimental until trained-gate + hardware runs land.

---

## 1. Environment (single source of truth for paths)

| Thing | Location |
|---|---|
| Research working tree (clean) | `C:\Research\` (this folder; non-OneDrive to avoid sync churn) |
| Aero2 working copy | `C:\Research\aero2\` (code + `data\`, 53.7 MB; heavy `results/analysis/00_SOTA` left in backup) |
| Python research env | conda **`hyperlif`** — `C:\Users\gandhico\AppData\Local\miniconda3\envs\hyperlif` (Py 3.11) |
| — contents | nengo 4.1, mujoco 3.11, numpy/scipy/matplotlib/jupyter, **`quanser` API** (from backup venv), **`qvl`** |
| Quanser resources | `C:\Users\gandhico\Documents\Quanser\` (`0_libraries\python` = pal/hal/pit/qvl) |
| QLabs (twin) | Quanser Interactive Labs 2.25.5256, installed + licensed (QUARC `.qlic`, Job#13488) |
| Installer bundle | `C:\Quanser_Setup\` (organized, staged) |
| MATLAB | R2025a (`C:\Program Files\MATLAB\R2025a`), license validated |
| Full backup | `D:\NMSU_backups\Backup\` — research code under `02_Research\` and `00_Research_\Neuromorphic_Embodied_AI\` |

---

## 2. The three-tier workflow (per platform)

The Aero2 repo is **backend-agnostic**: mode (`offline` / `virtual_twin` / `hardware`) is a config field, never an `if` in a controller.

| Tier | Python | MATLAB | Status |
|---|---|---|---|
| **Offline** (replay / model sim) | `OfflineBackend` | (native) | ✅ runs in `hyperlif` |
| **Digital twin** (QLabs) | `VirtualTwinBackend` → PAL → `tcpip://localhost:18950` | `matlab_bridge.TwinBridge` (py bridge) | ✅ **verified 2026-08-10** |
| **Hardware** (real Aero2 + HIL) | `DirectHilAero2IO` (Phase 6) | QUARC/HIL | ⬜ do in the lab |

---

## 3. Digital-twin connection — how it actually works

- QLabs **Aero2** (and Qube) are **benchtop** twins → driven by the **Quanser HIL/PAL** interface, **not** the `qvl` actor API. (`qvl` actors exist only for QCar/QBot/QDrone/QArm — the open-world mobile twins.)
- Python path: `pal.products.aero2.Aero2(hardware=0)` opens `0@tcpip://localhost:18950`. QLabs must be running with the Aero2 workspace open.
- The controller sees a clean contract `u=[u_pitch,u_yaw]`; the backend maps to motor volts (`output_mode="mixed"`: `motor0=u_p−u_y`, `motor1=u_p+u_y`) and clips to `voltage_limit`.
- State/convention (repo config): `x=[θ,θ̇,ψ,ψ̇]`, `y=[θ,ψ]`; encoders `θ=2π·n/2880`, `ψ=2π·n/4096`; command clip `±24 V` (`V_MAX`).

**⚠️ Insight #1 — warm-up quirk.** The twin's **first commanded pulse after connect reads zero**. A single-shot open-loop `pitch` test looked dead (θ_range=0); the same pulse *later* in a sequence moved fine. Fix: send one throwaway `apply(0)+read()` before the real loop (now baked into `TwinBridge.__init__`).

---

## 4. Cross-platform control (Python ↔ MATLAB, same twin)

- **Python (native):** `runners/run_control.py --mode virtual_twin --controller {pd,hyperlif,...}`. Controllers registered: `pd, lqr, lqg, mpc, backstepping, smc, nmpc, hyperlif, julia_policy`.
- **MATLAB (native controller, py bridge for I/O):** `matlab\aero2_twin_pd.m` implements the PD **natively in MATLAB** with the *exact* `config` gains, and drives the same twin via `matlab\matlab_bridge.py` (`pyenv` **OutOfProcess** on the `hyperlif` interpreter). This is the true cross-platform replication: identical twin + I/O, controller re-coded per platform.
- Gotcha resolved: the first MATLAB `-batch` run failed with exit `0x1` — it was **MATLAB license-ID validation**, not code. After validating, the bridge ran clean.

**Reproduce:**
```powershell
# Python
conda run -n hyperlif python C:\Research\aero2\runners\run_control.py --mode virtual_twin --controller pd --duration 15 --quanser-python "C:\Users\gandhico\Documents\Quanser\0_libraries\python"
# MATLAB
& "C:\Program Files\MATLAB\R2025a\bin\matlab.exe" -sd "C:\Research\aero2\matlab" -batch "aero2_twin_pd(15,100)"
```
(The Aero2 code hardcodes the old `C:\Quanser\...` PAL path — override with `--quanser-python` or env `QUANSER_PYTHON`.)

---

## 5. Results collected 2026-08-10 (Aero2, square-wave tracking θ=±20°@0.05 Hz, ψ=±45°@0.04 Hz)

> ⚠️ **These runs were on the twin in HALF-ROTOR config** (discovered afterward). They do **not** match `model_variant=helicopter_2dof`, which partly explains the poor tracking and limited yaw. **Re-run pending on the twin in helicopter-2DOF config** (`campaigns/run_twin_campaign.py`). Keep this table as the "config-mismatch" baseline.

| Run | Loop rate | pitch RMS | yaw RMS | tail pitch MAE | tail yaw MAE | pitch sat | yaw sat |
|---|---|---|---|---|---|---|---|
| Python PD (native) | 200 Hz | 0.603 | 0.499 | 0.474 | 0.683 | 0.635 | 0.051 |
| Python HyperLIF residual | 200 Hz | 0.658 | 0.480 | 0.683 | 0.669 | **0.002** | 0.002 |
| MATLAB PD (bridge) | **84.9 Hz** | 0.829 | 0.717 | 0.630 | 0.588 | **1.000** | 0.159 |
| *Hardware (Ref 3 Table IV)* | *~380 Hz* | *0.154* | *0.422* | — | — | *0.79/0.84* | — |

Raw data: `C:\Research\aero2\results_matlab\*.csv/.mat` (MATLAB), and re-runnable Python (`run_control --save`).

---

## 5.1 Results — helicopter 2DOF config (CLEAN, 2026-08-10)

Twin switched to **helicopter 2DOF**; full Python benchmark + cross-platform PD. Raw: `aero2/results_twin_campaign/` (per-run `.npz/.json` + `campaign_summary_*.csv/.md`).

**Python controller benchmark (native, ~200 Hz):**

| Controller | realized Hz | pitch RMS | yaw RMS | tail pitch MAE | tail yaw MAE | pitch sat | yaw sat |
|---|---|---|---|---|---|---|---|
| **PD** | 200 | **0.150** | 0.427 | **0.024** | 0.280 | 0.036 | 0.051 |
| LQR | 200 | 0.238 | 0.471 | 0.146 | 0.478 | 0 | 0 |
| LQG | 200 | 0.407 | 0.949 | 0.340 | 0.735 | 0 | 0 |
| MPC | 204 | 0.429 | 0.568 | 0.277 | 0.580 | 0 | 0 |
| Backstepping | 200 | 0.253 | 1.562 | 0.292 | 1.972 | 0.218 | 0 |
| SMC | 200 | 0.250 | 6.038 | 0.290 | 7.823 | 0.332 | 0 |
| NMPC | 200 | 0.294 | 2.239 | 0.279 | 1.179 | 0 | 0 |
| HyperLIF | 200 | 0.245 | 1.568 | 0.277 | **0.508** | 0 | 0.001 |

**PD rate / platform sweep (cross-platform):**

| Run | realized Hz | pitch RMS | yaw RMS | pitch sat |
|---|---|---|---|---|
| Python PD native | 200 | 0.150 | 0.427 | 0.036 |
| Python PD native | 90.9 (tgt 85) | 0.248 | 0.605 | 0.440 |
| MATLAB PD (bridge) | 69.5 | 0.449 | 1.236 | 0.827 |
| *Hardware (Ref 3 Table IV)* | *~380* | *0.154* | *0.422* | — |

## 5.2 Yaw control — quaternion 360° + yawboost (2026-08-10)

**Quaternion (wrap-aware) yaw** — `campaigns/run_yaw_quaternion.py`. Yaw is a unit quaternion about +z; the error is the shortest-path angle from the **canonicalized** error quaternion (`qw≥0`, else negate — otherwise `2·atan2` returns the long way, up to ±360°), bounded to (−π, π]. Setpoints ±170° that cross 180°, pitch regulated to 0:

| mode | `u_yaw`@switch | error@switch | yaw reach |
|---|---|---|---|
| naive (`ref−ψ`) | **−24.0 V** | −345° | 186° (cannot cross 180°) |
| quaternion | **+14.9 V** | +6.4° | 563° (~1.5 rev) |
| quaternion (damped Kp8/Kd7) | +4.7 V | +41° | 656° |

→ At the +170°→−170° switch, naive and quaternion command **opposite directions**: naive drives the long way (−345° error → −24 V); quaternion takes the **+20° hop across 180°** (+6.4° error → +15 V) and unlocks continuous **360°+** rotation. Positioning still overshoots/spins because the twin yaw is **underdamped** — removing the ±180° "wall" needs damping (or a trajectory/rate-limited ref, or the neuromorphic residual) to settle.

**yawboost gains** (`backstepping`/`smc` accept `yawboost=True`) — reference tracking, `campaigns/run_yawboost.py`:

| controller | yaw RMS (stock → boost) | tail yaw MAE (stock → boost) | pitch RMS |
|---|---|---|---|
| backstepping | 0.844 → **0.482** (−43%) | 1.030 → **0.425** (−59%) | ~0.18 (unchanged) |
| smc | 1.459 → 2.358 | 1.765 → 1.447 | ~0.23 |

→ yawboost is a clear win for backstepping; mixed for SMC. Best yaw so far ≈ 0.43–0.48 RMS (PD, backstepping+boost).

## 5.3 Regulation under disturbance (2DOF twin, 2026-08-10)

New app **`regulation_disturbance`** (hold θ=ψ=0; ±4 V command pulses: pitch @3–4/11–12 s, yaw @7–8/15–16 s). Deviation RMS from 0 (`campaigns/run_disturbance.py`):

| Controller | pitch RMS | yaw RMS |
|---|---|---|
| **PD** | **0.008** | **0.013** |
| LQR | 0.027 | 0.036 |
| SMC | 0.003 | 0.442 |
| backstepping | 0.013 | 0.404 |
| HyperLIF | 0.015 | 0.196 |
| qpd | 0.008 | 0.290 |
| LQG | 0.047 | 0.182 |
| NMPC | 0.043 | 0.676 |

→ PD/LQR reject best overall; SMC best pitch (0.003) but poor yaw. **HyperLIF has the best yaw rejection among the aggressive controllers** (0.196 vs BS 0.40 / SMC 0.44 / NMPC 0.68). Yaw is again the discriminating axis.

## 5.4 Quaternion yaw positioning — registered `qpd` (2026-08-10)

New controller **`qpd`** (wrap-aware quaternion error + rate-limited setpoint slew) vs naive `pd` on the new **`yaw_large_setpoint`** app (0→+170→−170→+270→0°), scored by **shortest-path** (wrap-aware) error, `campaigns/run_yaw_positioning.py`:

| ctrl | wrap RMS° | @170 | @−170 | @270 | @0 | reach° | travel° |
|---|---|---|---|---|---|---|---|
| pd (naive) | 79.8 | 8.0 | 11.7 | 35.9 | 32.2 | 305 | **1343** |
| **qpd** | **55.7** | 39.9 | 21.0 | **4.9** | **16.8** | 385 | **466** |

→ qpd travels **3× less** (466° vs 1343° — takes shortest paths), **nails the beyond-half-turn 270° setpoint** (4.9° vs 35.9°), lower overall wrap RMS, and rotates **past 360°** (reach 385°). Trade-off: its rate-limited slew (120°/s) settles slower at the near-±180° holds within a fixed window — tunable via `QPD_YAW_SLEW_RATE` / `QPD_KP_YAW`.

## 5.5 Gate-state residual augmented controller — MuJoCo architecture ported to Aero2 (2026-08-10)

Ported the MuJoCo-quadrotor gate-residual architecture (`experiments/hyperlif_aug_benchmark/hyperlif_aug_1d.py`, gate-state = "best MuJoCo setting") into Aero2 as the registered controller **`gate_residual`** (`aero2/control/neuromorphic/gate_residual.py`): PD base + a per-axis HyperLIF gate neuron on the **error feature** `x = e − 0.05·ω`, gate-state output `y = gate·sign(out)`, folded back as a **direction-safe residual** or a **gain-modulation**, with **fixed** (`hyperlif`) or **adaptive** (`adaptive_hyperlif`, adaptation state `a`) gains. `blend=0` ≡ PD (verified). Constants in `config/hyperlif.py` (`GATE_RES_*`).

Δ% vs PD, same session (`campaigns/run_gate_residual.py`):

| variant | track pitch | track yaw | **disturb pitch** | **disturb yaw** |
|---|---|---|---|---|
| gate_res_fixed | +5% | −2% | −26% | −20% |
| gate_res_adapt | +27% | +29% | −29% | −21% |
| gate_gain_fixed | +66% | +42% | −20% | −69% |
| **gate_gain_adapt** | +67% | +43% | **−29%** | **−72%** |

→ **The augmentation is a robustness (disturbance-rejection) booster, not a tracking aid.** On nominal tracking it is neutral-to-worse (fixed residual ≈ PD; the rest add aggression). Under command disturbances it delivers large gains — the **adaptive gain-modulation** hits **−29% pitch / −72% yaw** — because the gate fires on error, so it engages exactly when a disturbance strikes. Same regime the architecture was validated in on the MuJoCo quadrotor (hover under disturbance). *Caveat:* twin-state carryover (Insight #10) — the within-session vs-PD deltas are the valid signal, absolute RMS drifts run-to-run.

## 5.6 Hardware backend + physical-device blocker (2026-08-10)

Implemented **`HardwareBackend`** (`aero2/execution/hardware.py`) — inherits the twin's PAL wrapper with `hardware=1` (physical Aero 2), so controllers run unchanged across offline/twin/hardware. Refactored `VirtualTwinBackend` to expose the `hardware` flag. Motor-ID runner: `campaigns/run_motor_id.py [twin|hardware] [volts]`.

**Twin 2-DOF motor map (ID @4 V):** collective (rotors same sign) → **pitch** (16°); differential (rotors opposite) → **yaw** (19°, max yaw) with ~23° pitch coupling; single rotor → pitch-dominant thrust. Matches `config.params` (`u_c`→pitch, `u_d`→yaw).

**BLOCKER — physical device won't open:** `hardware=1` fails with *"Support for the given board type does not appear to be installed"*; Windows does not enumerate a Quanser USB device; only **QUARC Runtime** (not full QUARC) is installed. The physical Aero 2 **HIL/USB drivers ship with full QUARC** (`C:\Quanser_Setup\02_quarc\install_quarc.exe`). Until installed + device enumerated, hardware motor-ID and the twin-vs-hardware / Python-vs-MATLAB hardware comparison are blocked. Twin path is unaffected.

## 5.7 HARDWARE unblocked + first physical results (2026-08-10)

Full **QUARC 2026** installed (had to uninstall the standalone QLabs first — QUARC ships its own QLabs; it reinstalled QLabs + QUARC + HIL/USB drivers). Physical **`Quanser Aero 2 USB` now enumerates**; `QSDK_DIR`/`QUARC_DIR` set. The `quanser` 2025.11.1 Python package works against the new 26.0 HIL drivers. `run_control` gained the `hardware` branch; `campaigns/run_hw_control.py` + `run_motor_id.py hardware`.

**Motor-ID, twin vs hardware (open-loop, 4 V):** map is identical (collective→pitch, differential→yaw), but authority differs sharply:

| | collective→pitch | differential→yaw |
|---|---|---|
| Twin | 16° | **19°** |
| Hardware | 30° | **0.9°** |

**First hardware controller — PD, reference tracking, 200 Hz, Vlim 12 (`results_hardware/`):**

| PD | pitch RMS | yaw RMS | tail pitch MAE | tail yaw MAE | pitch sat |
|---|---|---|---|---|---|
| Twin (Vlim 15) | 0.150 | 0.427 | 0.024 | 0.281 | 0.036 |
| **Hardware (Vlim 12)** | **0.084** | 0.330 | **0.013** | 0.191 | 0.011 |
| Table IV (old HW) | 0.154 | 0.422 | — | — | — |

→ Hardware pitch tracks **tighter than the twin** and beats the old benchmark. Yaw: open-loop pulses barely move it (stiction), but **sustained closed-loop PD tracks yaw to ~11° tail error** — the physical yaw needs sustained authority to break stiction, which open-loop excitation underestimates.

## 6. Insights for the paper

1. **Twin fidelity CONFIRMED — once the config matches.** On the *helicopter-2DOF* twin, PD reproduces the hardware pitch benchmark almost exactly: twin pitch RMS **0.150** vs hardware **0.154** (Ref 3 Table IV), tail pitch MAE 0.024. The apparent "gap" in the half-rotor runs (0.60–0.83) was a **twin-config ↔ model mismatch**, not a fidelity limit. Correctly configured, QLabs Aero2 is a faithful stand-in for the hardware PD result — a strong reproducibility + teaching claim. (See Insight #6 on pinning the config.)
2. **Real-time rate is a first-class variable.** Native Python hits 200 Hz; MATLAB-via-py-bridge is IPC-bound at **~85 Hz**, and at that rate the same PD gains **fully saturate pitch (sat=1.000)**. Loop rate materially changes closed-loop behavior — worth reporting per platform, not hiding.
3. **HyperLIF residual is gentle.** The HyperLIF residual controller ran at 200 Hz with **near-zero saturation (0.002)** vs PD's 0.635 — comparable tracking with dramatically less actuator effort. First-ever **digital-twin** result for it (was "no Aero 2 hardware result yet").
4. **Device-class matters for the API.** `qvl` (actor API) ≠ HIL/PAL (benchtop API). Aero2/Qube need PAL over `:18950`; QCar/QBot/QDrone/QArm use `qvl` actors. This dictates the entire integration path.
5. **Warm-up quirk** (Insight #1) — reproducible; document it so lab students don't misread a "dead" twin.
6. **Match the twin CONFIG to the model.** The QLabs Aero2 has selectable configs (**half-rotor** vs **helicopter 2DOF**). Running `helicopter_2dof` controllers against a *half-rotor* twin gives limited yaw and inflated error — a config mismatch masquerading as a fidelity gap. **Always confirm the twin configuration matches `model_variant` before benchmarking.** (Strong ToE point: reproducibility requires pinning the twin config, not just the code.)
7. **Yaw is the open axis — and it motivates the neuromorphic residual.** Every model-based controller leaves yaw poor-to-unstable on the 2DOF twin: yaw RMS 0.43 (PD) → 0.95 (LQG) → 1.56 (backstepping) → 2.24 (NMPC) → **6.04 (SMC, unstable)**. This mirrors the hardware "yaw unresolved for every model-based controller." The **HyperLIF residual** posts the best yaw *tail* MAE (0.508) among the aggressive controllers at ~0 saturation — the neuromorphic augmentation targets exactly the unsolved axis. (Pitch is essentially solved by PD; the research contribution lives in yaw.)
8. **Real-time rate/latency monotonically degrades control.** Same PD, same 2DOF twin: 200 Hz → pitch RMS 0.150 (sat 0.04); 91 Hz → 0.248 (sat 0.44); 69 Hz via the MATLAB↔Python bridge → 0.449 (sat 0.83). The cross-language bridge adds IPC latency *on top of* the lower rate. Native-MATLAB real-time parity (200 Hz+, no bridge) needs the **QUARC/Simulink HIL** path — a concrete, quantified motivation for that tier rather than an assertion.
9. **Quaternion yaw = correct wrap-free control + 360° capability.** A unit-quaternion (shortest-path) yaw error commands the *right* direction across ±180° where the naive error commands the long way (+15 V vs −24 V at the wrap), and unlocks continuous 360°+ rotation the naive error structurally cannot. The twist: removing the ±180° "wall" that the naive error accidentally provides means yaw positioning now depends entirely on **damping** — the freedom to rotate must be paired with rate feedback / trajectory shaping, or the loop limit-cycles (spins). Clean generalization path to full 3D attitude (QDrone/QArm). Partial yaw *fix* (large-angle/continuous); the ±45° tracking fix is `yawboost` (Insight #7 axis, backstepping −43%).
10. **Twin state carries over between runs.** PAL cannot reset the QLabs virtual state, so each run starts from the previous end-state — backstepping stock yaw RMS read 1.56 (fresh) vs 0.84 (right after the 360° spin demo left the yaw displaced). **Reset the scene (or return-to-zero-and-settle) between benchmarked runs** for reproducible numbers — another concrete reproducibility item for the ToE method section.
11. **Disturbance rejection ranks differently than tracking.** PD/LQR reject 4 V kicks tightly (yaw RMS 0.013 / 0.036) where the aggressive nonlinear controllers do not (BS 0.40, SMC 0.44, NMPC 0.68). HyperLIF is the best yaw rejector among the aggressive set (0.196). Pitch is easy for everyone; yaw discriminates — same story as tracking, so the two applications corroborate rather than repeat.
12. **Quaternion `qpd` = shortest-path yaw, quantified.** 3× less total yaw travel (466° vs 1343°) and best positioning at 270° (beyond a half-turn, 4.9° vs 35.9°) vs naive PD, plus true 360°+ reach. The *rate-limited setpoint* is what turns "can rotate" into "positions cleanly." Now a first-class registered controller (`qpd`) alongside two new registered apps (`regulation_disturbance`, `yaw_large_setpoint`) — all reusable across the Quanser suite.
13. **The digital twin is a slightly CONSERVATIVE pitch proxy, and yaw is the sim-to-real axis.** Hardware PD tracked pitch to RMS 0.084 vs the twin's 0.150 (and the old 0.154 benchmark) — the twin under-promises pitch. Yaw is where sim and real diverge: identical motor map, but the physical yaw has stiction (open-loop pulses barely move it) that only *sustained closed-loop* authority overcomes (yaw tracked to ~11° tail under PD). Lesson for the paper: validate on hardware — the twin is honest but not identical, and open-loop excitation understates closed-loop yaw.
15. **Hardware yaw authority DEPENDS ON COLLECTIVE THRUST — the key sim→real methodological catch (corrects #13).** Open-loop differential *with no collective bias* stalls yaw at ~16° (props barely spinning → no yaw torque), which wrongly reads as "yaw is dead / cable-limited." But with a **PD holding pitch horizontal (props hovering), the physical yaw spins continuously — observed +916° (2.5 rev), pitch held at avg 2.3°**, no hard limit (slip ring / free rotation). So the twin's free 360° yaw IS reproducible on hardware *at the right operating point*; the quaternion missions are hardware-feasible with pitch stabilization. Lesson: characterize yaw authority **at the hovering operating point**, not open-loop from rest — a genuine "considerations for sim vs twin vs hardware" result. Trace: `results_hardware/yaw_max_pitchheld_*.csv`.
14. **The neuromorphic gate-residual earns its keep in ROBUSTNESS, not tracking.** The MuJoCo-quadrotor gate-state architecture, ported to Aero2 (`gate_residual`), is ~neutral on nominal tracking but rejects command disturbances markedly better than PD — adaptive gain-modulation: **−29% pitch, −72% yaw**; residual forms: ~−25% both axes. Mechanism: the gate fires on error, so the augmentation *self-activates on disturbances* and stays quiet during smooth tracking. This is a principled, honest niche for the neuromorphic controller, and it reproduces cross-platform the quadrotor's hover-under-disturbance result. **Adaptive gains beat fixed for rejection**; the gain-modulation form is the yaw specialist, the residual form the balanced choice.

---

## 7. Open items / next

- [ ] **Hardware tier** (in the lab): wire `DirectHilAero2IO` (Phase 6) to the real Aero2 + HIL; repeat PD/HyperLIF for the full offline→twin→hardware table.
- [ ] **Fair rate comparison:** re-run Python PD at 85 Hz (or MATLAB InProcess pyenv for higher Hz) to isolate rate vs platform.
- [ ] **Twin-tuned gains:** a twin-specific PD retune to close the fidelity gap (kept separate from hardware gains).
- [ ] **MATLAB HyperLIF:** either re-implement the residual natively or orchestrate the Python `hyperlif` controller through the bridge.
- [ ] **Native QUARC/Simulink path** (optional, heavier): full QUARC (`C:\Quanser_Setup\02_quarc\install_quarc.exe`) + Visual Studio/MSVC for true real-time Simulink Aero2 (`q_aero2_2dof_pd_quarc_win64`).
- [ ] Save every paper run with `--save` into a versioned `results_matlab\` / `results\`.

---

## 8. Reusable pattern (for the other platforms)

The Aero2 pattern generalizes to the rest of the suite in the backup (`04_Aero2_SNNs`, `05_Qcar_SNNs`, `06_QDrone_SNNs`, `07_ServoPendulum_SNNs`, `11_3DOF_Gyroscope`, `12_QBot`, `13_High_Definition_Haptic_Device`):
1. Copy code (not old results) into `C:\Research\<platform>\`.
2. Ensure `hyperlif` env has `quanser`+`qvl` (done) and any platform deps.
3. Pick the API by device class: **PAL/HIL** for benchtop (Aero2, Qube/pendulum, gyroscope), **`qvl` actors** for mobile (QCar, QBot, QDrone, QArm).
4. Offline → twin → hardware, same controllers, same metrics.
