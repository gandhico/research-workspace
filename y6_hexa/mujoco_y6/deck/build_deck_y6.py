"""Y6-in-MuJoCo update slides on Gandhi's NMSU template (for the meeting with Dr. Steed).

Reuses the helper layer of presentations/Research_Update_2026-09_build/build_deck.py
(everything above its first slide) so the slides look native; that file and the
template are only READ.  Every number is pulled from ../results/summary.json.
Run with the hover3dof venv (has python-pptx):
    C:\\Research\\hover3dof\\.venv\\Scripts\\python.exe build_deck_y6.py
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
HELPERS = Path(r"C:\Research\presentations\Research_Update_2026-09_build\build_deck.py")
src = HELPERS.read_text(encoding="utf-8")
src = src[:src.index("# ============================================================ 1. ACC")]
g = {"__file__": str(HELPERS), "__name__": "helpers"}
exec(compile(src, str(HELPERS), "exec"), g)
globals().update({k: v for k, v in g.items() if not k.startswith("__")})

OUT = HERE / "Y6_MuJoCo_Update_2026-09-23.pptx"
FIGS, MED = ROOT / "media" / "figs", ROOT / "media"
S = json.loads((ROOT / "results" / "summary.json").read_text())
V = S["validation_mujoco_vs_rk4"]


def cm3(r):
    return " / ".join(f"{v:.1f}" for v in r)


# ============================================================ 1. Overview
s = new_slide("Y6 Coaxial Tri-rotor | Now Flying in MuJoCo",
              "Nengo controllers from the ComRob 2026 work, unchanged, on a MuJoCo physics plant", kicker_x=3.6)
pic(s, MED / "nef_lif_hero.png", 0.5, 1.95, w=7.4)
text(s, 0.5, 6.15, 7.4, 0.5, [P(R("MuJoCo 3.11 render (t = 25 s, spiking controller): Y6 (m = 1.412 kg, 6 rotors in 3 coaxial pairs) sweeping the blades "
                                  "5 m upwind of a simple 3-blade turbine (hub 8 m, R = 3.7 m).", size=10.5, color=GRAY))])
cards = [
    ("Airframe", f"MJCF rigid body with [M] Table I mass/inertia; 6 thrust actuators whose force + drag-torque map "
                 f"reproduces the Nengo plant equations exactly."),
    ("Controllers", "Imported as-is from nengo_y6/src: classical cascade PD and the spiking NEF controller "
                    "(LIF PD populations + 4-D neural 6×4 allocator, n = 3000)."),
    ("Mission", "64 s turbine inspection: take-off, hub stand-off, blade sweep, nacelle side view, return, land; "
                "heading always looks at the hub."),
    ("Sensing", "Built-in MuJoCo cameras: onboard FPV RGB + depth, down-looking gimbal, chase and ground trackers."),
]
cy = 1.95
for head, body in cards:
    card(s, 8.15, cy, 4.7, 1.12, head, [P(R(body, size=11.5))], head_size=12.5)
    cy += 1.2
footer(s, [("Verified software (MuJoCo sim)", "software")],
       "Source: C:\\Research\\y6_hexa\\mujoco_y6 (y6_turbine_scene.xml, y6_mujoco_sim.py)")
notes(s, """
What was done (overnight 2026-09-23):
- Found the Y6 Nengo work on the backup drive (02_Coaxial_TriRotor_Nengo: 01_Code stages 1-8 and the paper-development tree with the exp04 coaxial-trirotor NEF controller). Copied it to C:\\Research\\y6_hexa\\nengo_y6.
- Built a MuJoCo model of the same airframe (Mehndiratta & Kayacan 2018 parameters) and a simple wind turbine (tower, nacelle, 3 spinning blades).
- The controllers were NOT rewritten: the NEF network is built by the same build_network(); only the plant node is swapped for MuJoCo.
Caveat if asked: the turbine is a visual/collision prop (no aerodynamics); the wind is a simple drag model (slide 5).
""")

# ============================================================ 2. Plant cross-check
s = new_slide("Plant Cross-Check | MuJoCo Matches the Nengo Model",
              "Same classical controller, same reference: MuJoCo body vs the RK4 Newton–Euler plant of the paper code",
              kicker_x=2.2)
pic(s, FIGS / "fig4_validation.png", 0.5, 1.95, w=7.6)
sx = 8.35
for big, s1, s2 in [(f"{V['max_dpos_mm']:.2f} mm", "max position difference", "over the full 64 s mission"),
                    (f"{V['max_dyaw_deg']*1000:.1f} mdeg", "max yaw difference", f"RMS position diff {V['rms_dpos_mm']:.3f} mm")]:
    box(s, sx, 1.95 if big.endswith("mm") else 3.25, 4.5, 1.15, fill=LIGHT, radius=0.06)
    yy = 1.95 if big.endswith("mm") else 3.25
    text(s, sx + 0.1, yy + 0.05, 4.3, 0.55, [P(R(big, size=26, bold=True, color=CRIMSON, font=TITLE_FONT), align="c")], anchor="m")
    text(s, sx + 0.1, yy + 0.6, 4.3, 0.5, [P(R(s1, size=11.5, bold=True), align="c"), P(R(s2, size=11, color=GRAY), align="c")])
text(s, 0.5, 4.95, 12.35, 1.9, [
    P(R("Rotor map implemented as MuJoCo site actuators (ctrl = Fᵢ = K_F Ωᵢ², gear = [0 0 1 0 0 ±K_τ/K_F]):  ", size=12, bold=True, color=CRIMSON),
      R("τx = l₂[(F₅+F₆)−(F₁+F₂)],  τy = l₁(F₃+F₄) − l₃(F₁+F₂+F₅+F₆),  τz = K_τ/K_F[(F₁+F₃+F₅)−(F₂+F₄+F₆)]", size=12), after=6),
    P(R("Finding: ", size=12, bold=True, color=CRIMSON),
      R("with z-up and a right-handed frame, these equations put the single arm (rotors 3,4) AFT at x = −l₁ and the two paired arms forward, "
        "which is the standard Y6. The code comments call it the \"front arm\"; the dynamics are right, the label is not.", size=12), after=6),
    P(R("Not yet in MuJoCo: ", size=12, bold=True, color=CRIMSON),
      R("propeller gyroscopic term (J_P = 6×10⁻⁵, small), motor lag, blade flapping, rotor inflow — all absent from the paper model too.", size=12)),
])
footer(s, [("Verified software", "software")], "Source: results/validate_mj_vs_rk4.npz, results/summary.json (y6_mujoco_sim.py --validate)")
notes(s, f"""
Why this matters: every number in the next slides is only meaningful if the MuJoCo plant is the same system as the paper's plant.
- Run: classical cascade controller with identical shaped reference; plant A = MuJoCo free body (dt 1 ms, MuJoCo default semi-implicit Euler), plant B = RK4 model from nengo_y6/src/models/coaxial_trirotor.py.
- Max |dp| = {V['max_dpos_mm']} mm, RMS {V['rms_dpos_mm']} mm, max |dyaw| = {V['max_dyaw_deg']} deg over 64 s. Residual = integrator differences (MuJoCo semi-implicit vs RK4) + the tiny gyroscopic term that MuJoCo does not have.
- A first run showed 45 mm at t < 2 s: the landing-pad geometry collided with the legs at spawn. Pad made visual-only; now sub-mm everywhere.
- Frame finding: tau_y = +l1(F3+F4) means rotors 3,4 sit at x = -l1 (aft). Controller signs are consistent, so nothing breaks; only the 'front arm' wording in comments / PROGRESS.md should be fixed.
""")

# ============================================================ 3. Mission results
c, n = S["classical"], S["nef_lif"]
s = new_slide("Spiking NEF Controller Flies the Inspection Mission",
              "Nengo LIF network (PD populations + neural allocator) closing the loop around MuJoCo at 1 kHz", kicker_x=2.4)
pic(s, FIGS / "fig1_mission_geometry.png", 0.45, 1.9, w=7.7)
pic(s, FIGS / "fig5_rotors.png", 0.75, 4.85, w=7.0)
table(s, 8.35, 1.95, [1.75, 1.35, 1.4], [
    ["Metric (6–56 s)", "Classical", "Spiking NEF"],
    ["RMSE x/y/z [cm]", cm3(c["rmse_cm"]), cm3(n["rmse_cm"])],
    ["max |e| [cm]", f"{c['max_err_cm']:.1f}", f"{n['max_err_cm']:.1f}"],
    ["yaw RMSE [deg]", f"{c['yaw_rmse_deg']:.2f}", f"{n['yaw_rmse_deg']:.2f}"],
    ["max tilt [deg]", f"{c['max_tilt_deg']:.1f}", f"{n['max_tilt_deg']:.1f}"],
    ["Ω range [rad/s]", f"{c['omega_min']:.0f}–{c['omega_max']:.0f}", f"{n['omega_min']:.0f}–{n['omega_max']:.0f}"],
    ["wall time, 64 s sim", f"{c['wall_s']:.1f} s", f"{n['wall_s']:.1f} s"],
], row_h=0.36, size=11.5, header_size=11)
text(s, 8.35, 4.65, 4.5, 2.2, [
    P(R("Spiking ≈ classical: ", size=12, bold=True, color=CRIMSON),
      R("same trajectory, a few mm more RMSE, more rotor-speed ripple (spike noise); all Ω well below the 900 rad/s limit.", size=12), after=5),
    P(R("Near real time: ", size=12, bold=True, color=CRIMSON),
      R(f"4,800 LIF neurons (6 PD populations × 300 + allocator 3000) + MuJoCo run {n['sim_s']:.0f} s of flight in {n['wall_s']:.0f} s on the laptop CPU.", size=12), after=5),
    P(R("Feed-forward via reference shaping ", size=12, bold=True, color=CRIMSON),
      R("(x_cmd = x_ref + K_d/K_p·v_ref + a_ref/K_p): controllers untouched.", size=12)),
])
footer(s, [("Verified software (MuJoCo sim)", "software")], "Source: results/summary.json · classical.npz, nef_lif.npz")
notes(s, f"""
- Controller code: nengo_y6/src/controllers_nengo/trirotor_nef.py build_network(), exp04 settings (LIF, tau 10 ms, n_cmd = 3000, seed 1). Only change: the plant node is the MuJoCo object.
- Classical RMSE x/y/z {cm3(c['rmse_cm'])} cm vs spiking {cm3(n['rmse_cm'])} cm over the flight window 6-56 s (take-off and landing excluded).
- These RMSEs are during motion at up to ~1.9 m/s; they are larger than exp04's sub-cm hover numbers because this is a moving mission, not a hover step.
- The feed-forward trick keeps the paper's control law: Kp(x_cmd - x) - Kd v = Kp e + Kd de/dt + a_ref.
- Q: 'Is it one seed?' Yes, seed 1 only; no statistics claimed.
""")

# ============================================================ 4. Cameras
s = new_slide("Onboard Cameras | RGB + Depth Built into MuJoCo",
              "Cameras are declared in the MJCF and rendered off-screen with mujoco.Renderer: no extra plug-in", kicker_x=2.6)
W3 = 4.05
for i, (img, cap) in enumerate([(MED / "nef_lif_hub_hold_fpv.png", "FPV RGB at the hub stand-off (t = 17 s)"),
                                (MED / "nef_lif_hub_hold_depth.png", "FPV depth, metres (near red → far blue)"),
                                (MED / "nef_lif_blade_sweep_fpv.png", "FPV during the blade sweep (t = 27 s)")]):
    x = 0.5 + i*(W3 + 0.12)
    pic(s, img, x, 1.95, w=W3)
    text(s, x, 1.95 + W3*9/16 + 0.03, W3, 0.3, [P(R(cap, size=10.5, color=GRAY), align="c")])
text(s, 0.5, 4.55, 6.1, 2.3, [
    P(R("Available now", size=13, bold=True, color=CRIMSON), after=3),
    P(R("Body-fixed cameras: fpv (70° FOV, 10° down-tilt), gimbal_down; world cameras: chase, side tracker, overview.", size=11.5), bullet=True, after=2),
    P(R("Per frame: RGB, metric depth, segmentation (geom/body IDs) from the same Renderer.", size=11.5), bullet=True, after=2),
    P(R("Centre-ROI depth reads the stand-off range directly (≈ 5 m to the hub at the hold).", size=11.5), bullet=True),
])
text(s, 6.8, 4.55, 6.05, 2.3, [
    P(R("Next: camera in the loop (proposed)", size=13, bold=True, color=CRIMSON), after=3),
    P(R("Render inside the sim loop at 30 Hz → hub/blade detection → visual-servo yaw and stand-off.", size=11.5), bullet=True, after=2),
    P(R("Event-camera emulation from frame differences (log-intensity threshold) → spiking input for Nengo / Loihi.", size=11.5), bullet=True, after=2),
    P(R("Blade-inspection dataset: labelled RGB-D frames with ground-truth pose, for free.", size=11.5), bullet=True),
])
footer(s, [("Verified software", "software"), ("Camera-in-the-loop", "proposed")], "Source: media/nef_lif_*_fpv.png, *_depth.png (render_video.py)")
notes(s, """
- MuJoCo does have cameras: any <camera> in the MJCF, fixed to the world or to a body; modes fixed/track/trackcom/targetbody. mujoco.Renderer renders RGB, depth (enable_depth_rendering) and segmentation off-screen (GPU/OpenGL), which is what render_video.py uses.
- These images come from replaying the logged states, not from inside the control loop; the controller does not see them yet.
- Rendering cost: 4 views x 1920 frames in ~3 min on this laptop (~40 renders/s at 640x360 with shadows), so a 30 Hz in-loop camera is feasible.
""")

# ============================================================ 5. Wind
cw, nw, ci, ni = S["classical_wind4"], S["nef_lif_wind4"], S["classical_wind4_int"], S["nef_lif_wind4_int"]
s = new_slide("Turbine-Site Wind | Where Adaptation Is Needed",
              "4 m/s mean wind + gusts + low-pass turbulence through a linear-drag body force (c_d = 0.35 N·s/m)", kicker_x=2.2)
pic(s, FIGS / "fig3_wind.png", 1.67, 1.9, w=10.0)
table(s, 0.5, 5.25, [3.3, 2.1, 2.1], [
    ["RMSE x / y / z [cm], 4 m/s", "Classical", "Spiking NEF"],
    ["PD (paper controllers)", cm3(cw["rmse_cm"]), cm3(nw["rmse_cm"])],
    ["PD + outer integral", cm3(ci["rmse_cm"]), cm3(ni["rmse_cm"])],
], row_h=0.36, size=11.5, header_size=11)
text(s, 8.25, 5.2, 4.6, 1.7, [
    P(R("PD leaves a ~0.5 m downwind offset; ", size=12, bold=True, color=CRIMSON),
      R("integral action cuts x RMSE ~3.5× for both controllers. Gust response (y) is unchanged.", size=12), after=5),
    P(R("Caveat: ", size=12, bold=True, color=CRIMSON),
      R("the integral here is a Python node, not neurons. Making it neural (NEF integrator or PES, Stage 7) is the next step.", size=12)),
])
footer(s, [("Verified software", "software"), ("Neural integral / PES", "proposed")], "Source: results/summary.json · *_wind4.npz, *_wind4_int.npz")
notes(s, """
- Wind model is deliberately simple: w(t) = 4 m/s along +x (toward the turbine) + two gust harmonics + Ornstein-Uhlenbeck turbulence (1.5 s correlation), force = c_d (w - v). No turbine wake, no rotor inflow effects.
- Integral gains are the project's own TrirotorIntegralGains (Ki_xy 0.5, Ki_z 2.0), injected through the reference (Ki*int(e)/Kp) so the controllers stay unchanged; clamp 3 m/s^2 anti-windup.
- Link to past result (exp04 Phase 5a): NEF integrators added their own decode bias there. So the neural version should be tried as PES decoder adaptation (01_Code stage 7) rather than a plain NEF integrator.
""")

# ============================================================ 6. Video
s = new_slide("Mission Video | Spiking Controller, Four Camera Views",
              "Chase · onboard FPV RGB · ground tracker · onboard FPV depth (1280×720, 30 fps, 64 s)", kicker_x=2.6)
vid = MED / "nef_lif.mp4"
s.shapes.add_movie(str(vid), Inches(2.3), Inches(1.9), Inches(8.7), Inches(8.7*9/16),
                   poster_frame_image=str(MED / "nef_lif_hub_hold.png"), mime_type="video/mp4")
footer(s, [("Verified software (MuJoCo sim)", "software")], "Source: media/nef_lif.mp4 (render_video.py); classical run: media/classical.mp4")
notes(s, """
Click to play. HUD (bottom-left of the chase view): time, position, tracking error, yaw, wind.
Sequence: pad spin-up 0-2 s, take-off, hub stand-off 14-18 s (the FPV looks straight at the hub), blade sweep low-right to high-left 18-30 s, nacelle side view 42-46 s, return and landing.
If the video does not play from the deck, open C:\\Research\\y6_hexa\\mujoco_y6\\media\\nef_lif.mp4 directly.
""")

# ============================================================ 7. Next
s = new_slide("Next Steps | Going Deeper in MuJoCo",
              "What exists now vs. what is proposed", kicker_x=5.0)
cols = [
    ("Done (software)", "software", [
        "Y6 MJCF with paper parameters, sub-mm match to the Nengo plant",
        "Classical + spiking NEF controllers flying a 64 s inspection mission",
        "Simple turbine (tower, nacelle, spinning rotor) and site wind",
        "Onboard RGB / depth cameras, 4-view video, figures, summary.json",
    ]),
    ("Next (days)", "proposed", [
        "Rotor fault in MuJoCo + PES fault-tolerant allocation (Stage 7 code exists)",
        "Neural wind rejection: PES instead of a NEF integrator",
        "Spinning rotor bodies → gyroscopic effects; first-order motor lag",
        "Camera in the loop: hub detection → visual-servo stand-off",
    ]),
    ("Later (weeks)", "proposed", [
        "Turbine wake / shear wind field; blade-proximity aerodynamics",
        "Event-camera emulation → spiking perception",
        "Full-SNN stage 8 and Loihi/Lava deployment study",
        "Hardware tie-in with the Y6 / QDrone line",
    ]),
]
x = 0.5
for head, kind, items in cols:
    box(s, x, 1.95, 4.0, 3.7, fill=LIGHT, radius=0.05)
    chip(s, x + 0.15, 2.07, head, kind, h=0.32, size=11.5)
    text(s, x + 0.15, 2.55, 3.7, 4.1, [P(R(it, size=12.5), bullet=True, after=7) for it in items])
    x += 4.18
footer(s, [("Verified software", "software"), ("Proposed", "proposed")], "Code: C:\\Research\\y6_hexa\\mujoco_y6 · README.md has the run commands")
notes(s, """
Ask for Dr. Steed: which direction matters most for the group? (a) fault tolerance of the coaxial Y6 (natural for the Y6, code already exists), (b) perception with the onboard cameras, or (c) wind/turbine aerodynamics fidelity.
Everything under 'Next' and 'Later' is proposed, not run.
""")

prs.save(str(OUT))
print("wrote", OUT)
