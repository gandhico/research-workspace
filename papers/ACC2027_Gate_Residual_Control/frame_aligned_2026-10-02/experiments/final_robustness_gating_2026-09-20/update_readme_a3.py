"""One-off: bring README.md up to date with amendment A3 / paper v14 (numbers are read from results/izh_a3_numbers.json).

Exact-one-match assertions; cannot be re-run on its own output.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
N = json.loads((HERE / "results" / "izh_a3_numbers.json").read_text(encoding="utf-8"))
RAIL = json.loads((HERE / "results" / "izh_a3_rails.json").read_text(encoding="utf-8"))
FLOOR = json.loads((HERE / "results_validation_izh" / "floor" / "floor_result.json").read_text(encoding="utf-8"))
nom, summ, hs = N["nominal"], N["summary"], N["hardstep_cells"]
sd_rel = max(v["sd_rel"] for v in FLOOR.values()) * 100
sd_pp = max(v["sd_pp_of_pdff"] for v in FLOOR.values())

p = HERE / "README.md"
s = p.read_text(encoding="utf-8")


def sub(old, new, tag):
    global s
    assert s.count(old) == 1, f"{tag}: {s.count(old)}"
    s = s.replace(old, new)
    print("ok", tag)


sub("archived was edited (the runner was copied, not modified, for amendment A2).",
    "archived was edited (the runner was copied, not modified, for amendments A2 and A3).\n"
    "Amendment A3 (2026-09-21) adds the Izhikevich basis under the same protocol: 33 campaign runs, 24 floor-ensemble runs and 6 validation/diagnostic runs\n"
    "(`REPORT_IZHIKEVICH_A3.md`); it enters the manuscript in v14.",
    "intro")

sub("| `audit_v13.py` | 46-check consistency audit of the manuscript against the data |",
    "| `audit_v13.py` | 46-check consistency audit of the v13 manuscript against the data (kept) |\n"
    "| `audit_v14.py` | audit of the v14 manuscript: the v13 checks plus 23 checks on the Izhikevich numbers, recomputed independently from the raw runs |\n"
    "| **`REPORT_IZHIKEVICH_A3.md`** | **complete report of the Izhikevich comparison** (protocol identity, validation and its CF2 caveat, results, mechanism, priors, disclosures, figures) |\n"
    "| `izh_adapter.py`, `run_izh_robustness.py`, `run_campaign_izh.py` | amendment A3: adapter around the archived Izhikevich augmentor, the sealed runner plus one controller choice, and the 33-case driver |\n"
    "| `validate_izh_runner.py`, `diagnose_cf2_*.py`, `sensitivity_izh.py`, `floor_izh.py` | A3 validation, the CF2 diagnosis, and the single-run floor of the spiking cell (24-run ensemble) |\n"
    "| `analyze_izh_a3.py`, `rail_fraction_izh.py`, `priors_a32.py`, `make_izh_report.py`, `make_table2_izh.py` | A3 analysis, the rails/effort statistics, the priors under the A3.2 rule, the report, and Table II's last block |\n"
    "| `make_izh_a3_figures.py`, `make_v14_figures.py` | reference figures for the advisors (`figures_out/izh_a3/`) and the two paper figures at v14 height (`figures_out/v14/`) |",
    "table")

new_section = f"""## Izhikevich-PES under the CMG protocol (amendment A3, 2026-09-21) — in the manuscript since v14

Same baseline (PD+ff rho = 3), score (true attitude), output gate, beta (X2 0.5, CF2 0.2), noise and burst definitions as the CMG rows; runner = the sealed
runner plus one controller choice. Reduced grid of 33 runs (nominal five missions x two airframes, gated; Hardstep ungated; realistic noise seeds 1-3 on Roll/Hard45/Hardstep;
hover bursts 1x), ~9 min. Details, validation and every table: **`REPORT_IZHIKEVICH_A3.md`**.

| rho = 3, gated | X2 | CF2 |
|---|---|---|
| Full3 / Hard45 vs PD+ff [%] (CMG in brackets) | {nom['x2/full3']['izh_gated_red']:+.1f} / {nom['x2/hard45']['izh_gated_red']:+.1f} ({nom['x2/full3']['cmg_red']:+.1f} / {nom['x2/hard45']['cmg_red']:+.1f}) | {nom['cf2-rotor/full3']['izh_gated_red']:+.1f} / {nom['cf2-rotor/hard45']['izh_gated_red']:+.1f} ({nom['cf2-rotor/full3']['cmg_red']:+.1f} / {nom['cf2-rotor/hard45']['cmg_red']:+.1f}) |
| Roll / Yaw360 vs PD+ff [%] (CMG) | {nom['x2/roll']['izh_gated_red']:+.0f} / {nom['x2/yaw360']['izh_gated_red']:+.0f} ({nom['x2/roll']['cmg_red']:+.0f} / {nom['x2/yaw360']['cmg_red']:+.0f}) | {nom['cf2-rotor/roll']['izh_gated_red']:+.0f} / {nom['cf2-rotor/yaw360']['izh_gated_red']:+.0f} ({nom['cf2-rotor/roll']['cmg_red']:+.0f} / {nom['cf2-rotor/yaw360']['cmg_red']:+.0f}) |
| five-mission geometric-mean error vs PD+ff | x{summ['x2']['geo_izh_mrad'] / summ['x2']['geo_pd_mrad']:.2f} (CMG x{summ['x2']['geo_cmg_mrad'] / summ['x2']['geo_pd_mrad']:.2f}) | x{summ['cf2-rotor']['geo_izh_mrad'] / summ['cf2-rotor']['geo_pd_mrad']:.2f} (CMG x{summ['cf2-rotor']['geo_cmg_mrad'] / summ['cf2-rotor']['geo_pd_mrad']:.2f}) |
| effort (RMS residual / bound), Izhikevich vs CMG | {summ['x2']['effort_izh']:.3f} vs {summ['x2']['effort_cmg']:.3f} (x{summ['x2']['effort_ratio']:.1f}) | {summ['cf2-rotor']['effort_izh']:.3f} vs {summ['cf2-rotor']['effort_cmg']:.3f} (x{summ['cf2-rotor']['effort_ratio']:.1f}) |
| Hardstep, ungated -> gated [%] | {hs['x2/izh_pes_ungated_b0p5']['red']:+.1f} -> {hs['x2/izh_pes_gated_b0p5']['red']:+.1f} | beta .2: diverges ({hs['cf2-rotor/izh_pes_ungated_b0p2']['err_mrad'] * 1e-3 * 57.29578:.0f} deg) -> {hs['cf2-rotor/izh_pes_gated_b0p2']['red']:+.1f} |

The residual sits on a +/- beta*l rail in {100 * RAIL['izh_rails_min']:.0f}-{100 * RAIL['izh_rails_max']:.0f} % of the samples on every mission (CMG: <= {100 * RAIL['cmg_rails_max']:.1f} %); its effort is mission-independent
(max/min {RAIL['izh_effort_range_max']:.1f}) while CMG's spans {RAIL['cmg_effort_range_min']:.0f}-{RAIL['cmg_effort_range_max']:.0f} and rank-follows the baseline error.
**Caveats.** The CF2 validation against the archived runner missed the declared 1e-9 tolerance (3.05e-4; X2 is bit-exact): the two runners differ by ~5e-20 N m in the residual
arithmetic, which the smooth CMG does not amplify and the spiking cell does (amendment A3.1). The measured single-run scatter of a spiking cell is {sd_rel:.1f} % of its error
({sd_pp:.1f} points of the PD+ff error, s.d.; 24-run ensemble), so differences below {3 * sd_pp:.0f} points are not interpreted (A3.2); the Roll/Yaw360 losses and the gate effects are far above that.

Reference figures (`figures_out/izh_a3/`, both airframes, title-free): `{{x2,cf2}}_{{hard45,hardstep,roll}}_attitude` (+ `_zoom` for Hardstep) and `..._neurons` (+ `_zoom`) — PD+ff, CMG ungated (wide, translucent),
CMG gated, Izhikevich gated (and ungated for Hardstep). The CF2 Hardstep zoom shows the ungated Izhikevich divergence at 10.2 s.

"""

sub("## Supplement (2026-09-21): Izhikevich-PES on the primary baseline — reference only, not a claim in the manuscript",
    new_section + "## Earlier supplement (2026-09-21, exploratory, archived runner, X2 only) — superseded by amendment A3 above",
    "supplement heading")
sub("Exploratory: deterministic, X2 only, one run per cell, not pre-registered.",
    "Exploratory: deterministic, X2 only, one run per cell, not pre-registered. Its numbers were seen before A3 was written (disclosed in A3); the ungated X2 cells are reproduced\nbit-exactly by the new runner (validation V1, V2), and the gated X2 cells are the A3 campaign.",
    "supplement note")
sub("& $py analyze_nominal.py ; & $py analyze_robustness.py ; & $py noise_numbers.py ; & $py audit_v13.py",
    "& $py analyze_nominal.py ; & $py analyze_robustness.py ; & $py noise_numbers.py ; & $py audit_v13.py\n"
    "# amendment A3 (Izhikevich, ~10 min + ~12 min for the floor ensemble)\n"
    "& $py validate_izh_runner.py ; & $py run_campaign_izh.py all ; & $py analyze_izh_a3.py ; & $py rail_fraction_izh.py ; & $py floor_izh.py ; & $py priors_a32.py\n"
    "& $py make_izh_a3_figures.py ; & $py make_izh_report.py ; & $py make_v14_figures.py ; & $py audit_v14.py   # audit needs the v14 paper built",
    "reproduce")
sub("* Do not claim a defect from a truncated display — verify with a script.",
    "* Do not claim a defect from a truncated display — verify with a script.\n"
    "* A spiking model is chaotic: last-bit differences between two correct runners moved a 45-s mean by 3e-4, and a 1e-14 rad initial offset by up to 1 %. Measure the single-run floor (24 runs, 12 min) before interpreting small differences.\n"
    "* Heredocs turned `\\times` into a TAB in a patch script (the audit caught it: \"2 imes10\" in a footnote). Write scripts with the file tools, and audit the compiled text, not just the source.",
    "lessons")
p.write_text(s, encoding="utf-8")
print("README updated")
