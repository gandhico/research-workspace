"""Freeze-time summary of every PPO run (reads results/<run>/metrics.csv, eval_gap.json, mujoco_eval.json).
Writes results/FROZEN_SUMMARY.json and results/FROZEN_SUMMARY.md and SHA-256 of sources and run outputs."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
R = HERE / "results"
RUNS = [  # (run dir, reward, arm label, line)
    ("v2pilot_mlp_s1", "v2", "mlp", "control"), ("v2pilot_cmg_acc_s1", "v2", "cmg_acc", "non-spiking"),
    ("v3A_mlp_bonus10", "v3 (sweep A)", "mlp", "control"), ("v3B_mlp_bonus10_crash5_smooth001", "sweep B", "mlp", "control"),
    ("v3_mlp_s1", "v3", "mlp", "control"), ("v3_cmg_acc_s1", "v3", "cmg_acc", "non-spiking"),
    ("v3_hyperlif_spike_s1", "v3", "hyperlif_spike", "spiking"),
    ("v4_mlp_s1", "v4", "mlp", "control"), ("v4_cmg_acc_s1", "v4", "cmg_acc", "non-spiking"),
    ("v4_hyperlif_spike_s1", "v4", "hyperlif_spike", "spiking"),
]


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def first(rows, cond):
    for r in rows:
        if cond(r):
            return round(f(r["env_steps"]) / 1e6, 1)
    return None


out = {}
for name, reward, arm, line in RUNS:
    p = R / name / "metrics.csv"
    if not p.exists():
        continue
    rows = list(csv.DictReader(p.open()))
    ev = [r for r in rows if r.get("eval_gates") not in (None, "")]
    last = rows[-5:]
    rec = dict(reward=reward, arm=arm, line=line, env_steps_M=round(f(rows[-1]["env_steps"]) / 1e6, 1),
               final_train_gates_per_episode=round(np.mean([f(r["ep_gates"]) for r in last]), 2),
               final_train_crash_rate=round(np.mean([f(r["crash_rate"]) for r in last]), 2),
               best_train_gates_per_episode=round(max(f(r["ep_gates"]) for r in rows), 2),
               first_eval_gate_M=first(ev, lambda r: f(r["eval_gates"]) >= 1),
               first_eval_past_splitS_M=first(ev, lambda r: f(r["eval_gates"]) >= 5),
               first_eval_lap_M=first(ev, lambda r: f(r["eval_gates"]) >= 7),
               best_eval_gates=int(max(f(r["eval_gates"]) for r in ev)) if ev else None,
               final_eval_gates=int(f(ev[-1]["eval_gates"])) if ev else None,
               best_lap_s=min([f(r["eval_first_lap_s"]) for r in ev if f(r.get("eval_first_lap_s"))] or [None]) if ev else None)
    if f(rows[-1].get("feature_mean")) is not None and arm != "mlp":
        rec.update(feature_mean=round(np.mean([f(r["feature_mean"]) for r in last]), 3),
                   feature_saturated=round(np.mean([f(r["feature_frac_saturated"]) for r in last]), 3),
                   feature_silent=round(np.mean([f(r["feature_frac_silent"]) for r in last]), 3),
                   event_rate_hz=round(np.mean([f(r["event_rate_hz"]) for r in last]), 2),
                   active_unit_frac=round(np.mean([f(r["active_unit_frac"]) for r in last]), 3))
    for extra in ("eval_gap.json", "mujoco_eval.json"):
        q = R / name / extra
        if q.exists():
            rec[extra.replace(".json", "")] = json.loads(q.read_text())
    out[name] = rec

sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
src = {p.name: sha(p) for p in sorted(HERE.glob("*.py"))}
outputs = {str(p.relative_to(R)): sha(p) for name in out for p in sorted((R / name).glob("*")) if p.is_file()}
(R / "FROZEN_SUMMARY.json").write_text(json.dumps({"runs": out, "source_sha256": src, "output_sha256": outputs}, indent=1))

md = ["| run | reward | arm (line) | steps (M) | train gates/ep (final) | crash (final) | 1st eval gate (M) | past split-S (M) | 1st lap (M) | best eval gates | best lap (s) | MuJoCo |",
      "|---|---|---|---|---|---|---|---|---|---|---|---|"]
for name, r in out.items():
    mj = r.get("mujoco_eval")
    mjs = (f"{mj['gates_in_order']} gates, {mj['collisions']} coll., " + (f"lap {mj['lap_time_s']} s" if mj.get('lap_time_s') else mj['termination'])) if mj else "--"
    md.append(f"| {name} | {r['reward']} | {r['arm']} ({r['line']}) | {r['env_steps_M']} | {r['final_train_gates_per_episode']} | "
              f"{r['final_train_crash_rate']} | {r['first_eval_gate_M']} | {r['first_eval_past_splitS_M']} | {r['first_eval_lap_M']} | "
              f"{r['best_eval_gates']} | {r['best_lap_s']} | {mjs} |")
gap = ["", "| run | det. official | det. distributed | stoch. official | stoch. distributed |", "|---|---|---|---|---|"]
for name, r in out.items():
    g = r.get("eval_gap")
    if g:
        cell = lambda k: f"{g[k]['gates_mean']} gates, lap {100 * g[k]['frac_full_lap']:.0f}%, crash {100 * g[k]['crash_rate']:.0f}%"
        gap.append(f"| {name} | {cell('det_official')} | {cell('det_distributed')} | {cell('stoch_official')} | {cell('stoch_distributed')} |")
neu = ["", "| run | feature mean | saturated | silent | event rate (Hz/unit) | active units |", "|---|---|---|---|---|---|"]
for name, r in out.items():
    if "feature_mean" in r:
        neu.append(f"| {name} | {r['feature_mean']} | {r['feature_saturated']} | {r['feature_silent']} | {r['event_rate_hz']} | {r['active_unit_frac']} |")
(R / "FROZEN_SUMMARY.md").write_text("\n".join(md + gap + neu) + "\n")
print("\n".join(md + gap + neu))
