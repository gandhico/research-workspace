# Final robustness and saturation-gating campaign (2026-09-20)

Continues the work Codex left in this folder (a runner and two 0.1-s smoke runs; no data, never validated against the
archive). 597 confirmatory runs, 19 exploratory runs and 20 validation runs (`count_runs.py`); everything is reproducible from the scripts below, and nothing
archived was edited (the runner was copied, not modified, for amendments A2 and A3).
Amendment A3 (2026-09-21) adds the Izhikevich basis under the same protocol: 33 campaign runs, 24 floor-ensemble runs and 6 validation/diagnostic runs
(`REPORT_IZHIKEVICH_A3.md`); it enters the manuscript in v14.

## Read in this order

| file | what it is |
|---|---|
| `PREREGISTRATION.md` | hypotheses, decision rules and priors, **sealed with SHA-256 before any campaign result**; dated amendments A1, A2 and their addenda are appended, including one clarification I wrote after seeing selection-stage results (disclosed in place) |
| `run_validation.py` → `results_validation/` | **validation gate**: 20 cells vs the archived Table II, worst relative error **5.0e-15** (bit-identical) |
| `run_final_robustness.py` | the runner (Codex's, plus one added exploratory gate mode) — sealed while the noise campaign ran |
| `run_a2_robustness.py` | copy of the runner with the two A2 gate modes (rotor flag, thrust starvation) |
| `run_campaign.py`, `run_campaign_a1.py`, `run_campaign_a2.py`, `run_chain*.py` | frozen plans and drivers (`<= 4` workers; memory is the limit) |
| `build_final_csv.py` → `results/final_*.csv` | assembles the final tables: X2 primary = gated beta 0.5, CF2 primary = gated beta 0.2 (A2), CF2 beta 0.5 kept as `cmg_pes_gated_b05` |
| `analyze_*.py`, `hardstep_profile.py`, `noise_numbers.py`, `cite_numbers.py`, `check_starvation_all_seeds.py` | analysis; every number in the paper comes from these |
| `make_table2.py` | regenerates Table II's primary block from the CSVs |
| `audit_v13.py` | 46-check consistency audit of the v13 manuscript against the data (kept) |
| `audit_v14.py` | audit of the v14 manuscript: 71 checks: the v13 ones plus 25 new (22 on the Izhikevich numbers, recomputed independently from the raw runs; 3 on the edited text) |
| **`REPORT_IZHIKEVICH_A3.md`** | **complete report of the Izhikevich comparison** (protocol identity, validation and its CF2 caveat, results, mechanism, priors, disclosures, figures) |
| `izh_adapter.py`, `run_izh_robustness.py`, `run_campaign_izh.py` | amendment A3: adapter around the archived Izhikevich augmentor, the sealed runner plus one controller choice, and the 33-case driver |
| `validate_izh_runner.py`, `diagnose_cf2_*.py`, `sensitivity_izh.py`, `floor_izh.py` | A3 validation, the CF2 diagnosis, and the single-run floor of the spiking cell (24-run ensemble) |
| `analyze_izh_a3.py`, `rail_fraction_izh.py`, `priors_a32.py`, `make_izh_report.py`, `make_table2_izh.py` | A3 analysis, the rails/effort statistics, the priors under the A3.2 rule, the report, and Table II's last block |
| `make_izh_a3_figures.py`, `make_v14_figures.py` | reference figures for the advisors (`figures_out/izh_a3/`) and the two paper figures at v14 height (`figures_out/v14/`) |
| `figlib.py`, `make_paper_figures.py`, `make_noise_figure.py` → `figures_out/` | title-free figures in the *attitude_detail* and *neurons* formats (index below) |

## Results

**Validation.** The new runner reproduces the archived rho = 3 block of Table II bit for bit, including CF2 at beta = 0.05.

**H2 — CF2 authority (pre-registered prediction: holds noise-free).** Gated, beta = 0.5: CF2 geo-mean reduction
**36.5 %** (was 6.5 % at the beta = 0.05 the paper had used but not disclosed); X2 37.3 % (was 35.6 %). The gate acts in
<= 0.04 % of samples away from Hardstep; those cells change by <= 0.1 %.

**H1 — Hardstep (prediction: fails on mean error).** Gated vs PD+ff: X2 **−2.05 %**, CF2 −1.23 % (ungated: −17.0 % /
divergence). Braking is helped (0.25–0.75 s after a step, −0.13 deg of the X2 mean), the settling tail is hurt
(0.75–1.5 s, +0.40 deg) once the baseline has left its box, so no rule conditioned on saturation can remove it.

**A1 — lowering the load threshold** (X2 Hardstep, noise-free): 1.0 / 0.75 / 0.5 / 0.25 / 0.001 → −2.05 / −1.21 / −0.16 /
+0.11 / **+0.32 %**; at 0.001 the gate blocks 79 % of samples and recovers the baseline's settled error (0.186 vs
0.185 deg). Twelve gate configurations in all ranged from −2.1 % to +0.3 %: **parity is the ceiling.** No variant met the
2 % promotion margin.

**H3 — noise (true-attitude error, paired seeds; 5 moderate + 10 realistic).** Against the tuned baseline the benefit
survives only where the baseline error exceeds the noise floor. Realistic level:

| | Roll | Full3 | Hard45 | Hardstep | Yaw360 | geo |
|---|---|---|---|---|---|---|
| X2 (beta 0.5, gated) | −4.2 | +11.3 | +10.8 | −2.6 | −5.3 | +2.3 |
| CF2 (beta 0.2, gated) | −0.4 | +3.9 | +4.0 | −0.3 | −2.2 | +1.0 |
| CF2 (beta 0.5, gated) | — | +8.7 | +9.3 | **diverges 15/15** | — | — |

Full3/Hard45 positive in every seed (s.d. < 0.2 pp); Roll/Yaw360 negative in every seed (0/10 positive), but tiny in
absolute terms (<= 0.07 mrad). The old "all noisy reductions positive" claim was against fixed PD, whose errors sit far above
the floor.

**Why CF2 beta = 0.5 diverges under noise** (`diagnose_cf2_noise.py`, `check_starvation_all_seeds.py`): at the 9 s step the
requested collective thrust reaches 0.66 N against 0.525 N realized; every rotor saturates, realized torque falls short,
tilt grows, tilt compensation asks for more thrust. The residual is same-sign with u0 (or on an unsaturated axis), so the
torque-box gate never fires. Rotor-saturated share equals thrust-starved share in all seeds (61–79 % vs 0.3 % for PD+ff).

**A2 — repair attempts (pre-registered, seeds 1–2 for development, the rest held out).** Gates that also block on the
allocator's saturation flag or on thrust starvation **still diverge** (ratio 6.3 / 7.8 to PD+ff) although they block the
residual in 68–82 % of samples: once saturation starts the loop is already in a runaway. The exact gate at **beta = 0.2 is
safe** (ratio 1.00 to PD+ff), beta = 0.1 also; by the pre-declared rule beta = 0.2 wins (noise-free geo 22.4 % vs 13.0 %).
Held-out confirmation: all 13 CF2 Hardstep noise runs at 1.002–1.004x PD+ff; every nominal CF2 cell at least as good as the
published configuration. **Adopted for CF2.**

**H4 — disturbance bursts (Hover, rho = 3).** Burst-phase error: X2 −14.4 % (24.0 / 13.3 % at 0.5x / 2x), CF2 (beta 0.2)
−5.9 % (6.5 / 4.7 %); at beta 0.5 it would be −13.7 %, at the old 0.05 only −1.5 %. X2 quiet-phase error rises at 0.5x
(0.021 → 0.036 deg). Hover never saturates: the gate is inert here.

## Figure index (`figures_out/`, all title-free; PDF + 300-dpi PNG)

| file | shows |
|---|---|
| `x2_hard45_attitude_rho3` / `_compact` | error + roll/pitch/yaw, PD+ff vs CMG–PES (compact = the version in the paper) |
| `x2_hard45_neurons_rho3` | membrane, gate, activity, residual, decoder norm; all six gates latch by 9 s |
| `x2_hardstep_gate_zoom`, `cf2-rotor_hardstep_gate_zoom` | one step: log error and binding-axis torque, blocked intervals shaded (CF2 panel is beta 0.5) |
| `{x2,cf2-rotor}_hardstep_attitude_rho3` | full 45 s Hardstep, three arms |
| `{x2,cf2-rotor}_hover_disturbance_attitude_rho3`, `_neurons_rho3` | bursts shaded; CF2 shows the selected beta = 0.2 |
| `{x2,cf2-rotor}_hard45_noise_attitude_rho3`, `_neurons_rho3` | one realistic-noise seed |
| `noise_{realistic,moderate}_paired_reductions` | per-seed reductions vs the noise-free value, both platforms |

`../final_clean_figures_2026-09-20/` (Codex) is superseded: its inset overlapped the error trace and its 2:3 shape was too tall.

## Izhikevich-PES under the CMG protocol (amendment A3, 2026-09-21) — in the manuscript since v14

Same baseline (PD+ff rho = 3), score (true attitude), output gate, beta (X2 0.5, CF2 0.2), noise and burst definitions as the CMG rows; runner = the sealed
runner plus one controller choice. Reduced grid of 33 runs (nominal five missions x two airframes, gated; Hardstep ungated; realistic noise seeds 1-3 on Roll/Hard45/Hardstep;
hover bursts 1x), ~9 min. Details, validation and every table: **`REPORT_IZHIKEVICH_A3.md`**.

| rho = 3, gated | X2 | CF2 |
|---|---|---|
| Full3 / Hard45 vs PD+ff [%] (CMG in brackets) | +5.7 / +9.8 (+12.4 / +13.8) | +6.3 / +6.7 (+5.4 / +7.3) |
| Roll / Yaw360 vs PD+ff [%] (CMG) | -812 / -1455 (+78 / +42) | -84 / -1026 (+60 / +20) |
| five-mission geometric-mean error vs PD+ff | x2.62 (CMG x0.63) | x1.79 (CMG x0.78) |
| effort (RMS residual / bound), Izhikevich vs CMG | 0.362 vs 0.032 (x11.4) | 0.144 vs 0.015 (x9.5) |
| Hardstep, ungated -> gated [%] | -16.9 -> -1.5 | beta .2: diverges (119 deg) -> -0.5 |

The residual sits on a +/- beta*l rail in 35-48 % of the samples on every mission (CMG: <= 0.8 %); its effort is mission-independent
(max/min 1.1) while CMG's spans 120-220 and rank-follows the baseline error.
**Caveats.** The CF2 validation against the archived runner missed the declared 1e-9 tolerance (3.05e-4; X2 is bit-exact): the two runners differ by ~5e-20 N m in the residual
arithmetic, which the smooth CMG does not amplify and the spiking cell does (amendment A3.1). The measured single-run scatter of a spiking cell is 1.4 % of its error
(1.3 points of the PD+ff error, s.d.; 24-run ensemble), so differences below 4 points are not interpreted (A3.2); the Roll/Yaw360 losses and the gate effects are far above that.

Reference figures (`figures_out/izh_a3/`, both airframes, title-free): `{x2,cf2}_{hard45,hardstep,roll}_attitude` (+ `_zoom` for Hardstep) and `..._neurons` (+ `_zoom`) — PD+ff, CMG ungated (wide, translucent),
CMG gated, Izhikevich gated (and ungated for Hardstep). The CF2 Hardstep zoom shows the ungated Izhikevich divergence at 10.2 s.

## Earlier supplement (2026-09-21, exploratory, archived runner, X2 only) — superseded by amendment A3 above

The paper's Izhikevich rows are on the fixed-PD baseline. To plot CMG-PES ungated and gated against it on the *same*
baseline, `run_izh_supplement.py` runs the ARCHIVED runner (`run_mujoco_nef_baselines.py`, the one that produced the paper's
rho = 3 CMG rows) with `--controller nengo-izhikevich-pes` and the same arguments (beta 0.5, PD+ff rho = 3, X2, five missions).
`validate_adapter.py` shows the archived trace schema, converted by `figlib_multi.load_archived`, reproduces this campaign's
CMG run exactly (Euler 1e-13 deg, zero difference in error, residual, membrane), so the arms are directly comparable.
Exploratory: deterministic, X2 only, one run per cell, not pre-registered. Its numbers were seen before A3 was written (disclosed in A3); the ungated X2 cells are reproduced
bit-exactly by the new runner (validation V1, V2), and the gated X2 cells are the A3 campaign.

| X2, rho = 3 | Roll | Full3 | Hard45 | Hardstep | Yaw360 | geo |
|---|---|---|---|---|---|---|
| CMG-PES ungated vs PD+ff [%] | +78.4 | +12.4 | +13.8 | −17.0 | +41.8 | +35.6 |
| CMG-PES gated vs PD+ff [%] | +78.4 | +12.4 | +13.8 | −2.0 | +41.8 | +37.3 |
| Izhikevich-PES vs PD+ff [%] | **−812** | +5.3 | +6.8 | −16.9 | **−1455** | −171 |
| effort, CMG / Izhikevich (RMS residual / bound) | 0.003 / 0.371 | 0.023 / 0.373 | 0.023 / 0.373 | 0.109 / 0.337 | 0.001 / 0.370 | |

Izhikevich's residual chatters between its +/- beta*l rails at ~0.37 of the bound **whatever the baseline error**, so on the
missions the tuned baseline already tracks (Roll 0.34, Yaw360 0.20 mrad) it raises the error to ~3 mrad, and it recovers only
about half of CMG's gain on Full3/Hard45. On the weak fixed-PD baseline this cost is hidden inside a large error, which is
why the paper's Izhikevich rows look competitive.

Figures (`figures_out/izh_compare/`, title-free; PD+ff baseline, CMG ungated (wide, translucent), CMG gated, Izhikevich):
`x2_{hard45,hardstep,roll}_attitude_ungated_gated_izhikevich` (error + roll/pitch/yaw, one window; `_zoom` for Hardstep with a log
error axis), and `x2_{hard45,hardstep,roll}_neurons_ungated_gated_izhikevich` (+ `_zoom`): one column per arm because the units
differ (CMG membrane/gate are dimensionless; Izhikevich membrane is in mV, its "gate" row is the recovery variable u, and its
"activity" is a 5-ms low-pass spike trace that exceeds 1 — the clip is applied after decoding); residual and decoder norm share axes.
The 5-ms sampling aliases the sub-millisecond spikes, so the raw Izhikevich state rows look dense.
On Hard45 and Roll gated = ungated (gate inert), so the two CMG lines coincide; Hardstep is where they differ.
On Roll the CMG units never latch (gate r stays 0, activity at its resting 0.37), so the residual is ~0 and the decoder is flat —
the mechanism behind CMG's low effort when nothing needs correcting — while Izhikevich chatters between its rails throughout.
On Hard45/Hardstep all six CMG gates latch at 1 within the first seconds and the residual is smooth, pulsing at step onsets.

## Ladder figure — the old `attitude_detail` layout with the baseline ladder (2026-09-21)

`make_ladder_figure.py` -> `figures_out/ladder/{x2,cf2}_hard45_ladder_{A,B,C}.{png,pdf,json}` (title-free). Rows 1-4 (error, roll, pitch, yaw): the three PD versions of the
paper's ladder in blues (original fixed PD, PD+ff rho=1, PD+ff rho=3; light -> dark = weak -> strong) and the CMG-PES run on each in reds; the controller signals are
semi-transparent and the reference is an opaque black dashed line on top. Rows 5-6 (quaternion, rotor forces): the best CMG run of the mission = the lowest mean error
of the three CMG versions drawn (PD+ff rho=3 + CMG-PES, gated: 0.52 deg on X2, 0.46 deg on CF2). A = log error axis, B = linear (the original look), C = A plus an 8-s zoom column;
`cf2_hard45_ladder_A_beta05` draws CF2's noise-free beta = 0.5 run (0.41 deg, better on Hard45 but not the adopted setting: it diverges on Hardstep under noise).
Every trace is one of the runs behind Table II; the script asserts that each mean shown equals the paper's table value (relative 1e-4; the CMG-on-PD run in `matched_45s`
and the one behind the master table are two executions of the same configuration, 3e-8 apart on X2 and 2e-6 on CF2) and writes the numbers and source paths to the `.json`.
It also builds the other four missions on both airframes (checked 10/10); `--titles` restores the old bold section titles, `--cf2-beta 0.5` selects the beta = 0.5 run.

## Reproduce

```powershell
$root = 'C:\Research\papers\ACC2027_Gate_Residual_Control'
$py   = "$root\.venv\Scripts\python.exe"
cd "$root\experiments\final_robustness_gating_2026-09-20"
& $py run_validation.py                              # must print PASS first
& $py run_campaign.py --campaign nominal             # 35 runs, ~6 min
& $py run_campaign.py --campaign hardstep-development
& $py run_campaign.py --campaign disturbance         # 21 runs
& $py run_campaign.py --campaign noise               # 450 runs, ~95 min at 4 workers
& $py run_campaign_a1.py                             # note: threshold 0 is invalid; the limit case is 0.001 (see prereg addendum)
& $py run_campaign_a2.py dev                         # then: nominal <variant>, confirm <variant>, disturbance <v>, noise_rest <v>
& $py build_final_csv.py
& $py analyze_nominal.py ; & $py analyze_robustness.py ; & $py noise_numbers.py ; & $py audit_v13.py
# amendment A3 (Izhikevich, ~10 min + ~12 min for the floor ensemble)
& $py validate_izh_runner.py ; & $py run_campaign_izh.py all ; & $py analyze_izh_a3.py ; & $py rail_fraction_izh.py ; & $py floor_izh.py ; & $py priors_a32.py
& $py make_izh_a3_figures.py ; & $py make_izh_report.py ; & $py make_v14_figures.py ; & $py audit_v14.py   # audit needs the v14 paper built
& $py make_ladder_figure.py --platforms x2 cf2-rotor --variants A B C     # ladder figure (add --missions ... for the others)
& $py make_paper_figures.py hard45 hardstep_zoom disturbance noise ; & $py make_noise_figure.py realistic moderate
```

## Lessons (also in memory)

* Bash heredocs on this machine mangle backslashes; put Python and LaTeX edits in files and assert exactly one match per replacement.
* A wait loop that greps a pattern the log never prints (`[ 35/35]` has a space) cost 10 minutes; a `Stop-Process` filter matched its own command line.
* Do not claim a defect from a truncated display — verify with a script.
* A spiking model is chaotic: last-bit differences between two correct runners moved a 45-s mean by 3e-4, and a 1e-14 rad initial offset by up to 1 %. Measure the single-run floor (24 runs, 12 min) before interpreting small differences.
* Heredocs turned `\times` into a TAB in a patch script (the audit caught it: "2 imes10" in a footnote). Write scripts with the file tools, and audit the compiled text, not just the source.
