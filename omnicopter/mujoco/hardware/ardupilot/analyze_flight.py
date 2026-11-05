"""Analyse one ground-station session from flight_logs (read-only): step 4 of the feedback cycle.

    python analyze_flight.py                    # newest session in flight_logs
    python analyze_flight.py 20261104_190320    # a given session
    python analyze_flight.py 20261104_190320 --png   # also save reports/flight_<session>_<n>.png

For every armed span in which the motors left 1500 us it prints:
  * lift-off time (OptiTrack height >= 5 mm above the pre-arm ground), peak height;
  * roll/pitch milestones and the tilt at the end of the span;
  * each rotor's output on its hover side, in % of the 500 us range, at lift-off and at the end;
  * left/right, front/back and top/bottom balance;
  * the strapped/tethered pass criteria of the cycle: no rotor above 80 %, left and right within 10 %.

Rotor faces come from the twin (AP frame: forward = twin +z, right = -y, down = +x); hover signs
come from the throttle column of generated/omnidrone_6dof_mixer.json.
Nothing in flight_logs is ever written or deleted.
"""
import argparse
import csv
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGS = HERE / "flight_logs"
MIXER = HERE / "generated" / "omnidrone_6dof_mixer.json"
FACES = {"left": (3, 4, 7, 8), "right": (1, 2, 5, 6), "front": (2, 4, 6, 8), "back": (1, 3, 5, 7),
         "top": (1, 2, 3, 4), "bottom": (5, 6, 7, 8)}
CORNER = {1: "top right back", 2: "top right front", 3: "top left back", 4: "top left front",
          5: "bottom right back", 6: "bottom right front", 7: "bottom left back", 8: "bottom left front"}
MAX_ROTOR_PCT = 80.0
MAX_LR_IMBALANCE = 0.10
LIFT_M = 0.005


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return math.nan


def hover_signs():
    meta = json.loads(MIXER.read_text())
    f = meta["factors_by_ap_motor"]
    return [1 if f[f"Motor{i}"][3] > 0 else -1 for i in range(1, 9)]


def effort(us, signs):
    """Output on the hover side, % of the 500 us range (negative = pushing the weak way)."""
    return [(u - 1500) * s / 5.0 for u, s in zip(us, signs)]


def side_mean(eff, side):
    return sum(eff[i - 1] for i in FACES[side]) / 4.0


def load(stamp):
    tele = list(csv.DictReader(open(LOGS / f"telemetry_{stamp}.csv", newline="")))
    moc_path = LOGS / f"mocap_{stamp}.csv"
    moc = list(csv.DictReader(open(moc_path, newline=""))) if moc_path.exists() else []
    return tele, moc


def spans(tele):
    """Armed spans in which at least one output left 1500 us."""
    out, cur = [], None
    for r in tele:
        if r["armed"] == "1" and r["servo1_us"]:
            us = [int(num(r[f"servo{i}_us"])) for i in range(1, 9)]
            spinning = any(u != 1500 for u in us)
            if spinning:
                if cur is None:
                    cur = {"t0": num(r["time_s"]), "rows": []}
                cur["rows"].append((num(r["time_s"]), us))
                continue
        if cur is not None:
            out.append(cur)
            cur = None
    if cur is not None:
        out.append(cur)
    return out


def report_span(n, sp, moc, signs, t_start):
    t0, rows = sp["t0"], sp["rows"]
    t1 = rows[-1][0]
    print(f"\n--- Motor-on attempt {n}: t = {t0 - t_start:.2f} .. {t1 - t_start:.2f} s "
          f"({t1 - t0:.1f} s, {len(rows)} output rows)")
    base = [r for r in moc if t0 - 2.0 <= num(r["time_s"]) <= t0 - 0.5 and r["valid"] == "1"]
    seg = [r for r in moc if t0 <= num(r["time_s"]) <= t1 + 0.2 and r["valid"] == "1"]
    lift_t = None
    if base and seg:
        g = sum(-num(r["d_m"]) for r in base) / len(base)
        h = [(num(r["time_s"]), -num(r["d_m"]) - g, math.degrees(num(r["roll_rad"])),
              math.degrees(num(r["pitch_rad"]))) for r in seg]
        lift = next((x for x in h if x[1] >= LIFT_M), None)
        peak = max(h, key=lambda x: x[1])
        lift_t = lift[0] if lift else None
        print(f"  lift-off: {'none' if lift is None else f'+{lift[0] - t0:.2f} s after the motors started'}; "
              f"peak height {100 * peak[1]:.1f} cm at +{peak[0] - t0:.2f} s")
        for th in (5, 10, 20, 30):
            hit = next((x for x in h if math.hypot(x[2], x[3]) >= th), None)
            if hit:
                print(f"  tilt >= {th:2d} deg at +{hit[0] - t0:.2f} s (roll {hit[2]:+.1f}, pitch {hit[3]:+.1f})")
        last = h[-1]
        print(f"  at the end: roll {last[2]:+.1f} deg, pitch {last[3]:+.1f} deg, height {100 * last[1]:.1f} cm")
    else:
        print("  no OptiTrack rows around this span")

    def at(t):
        """Outputs of the last telemetry row at or before t (the command that produced the state)."""
        before = [r for r in rows if r[0] <= t]
        return (before[-1] if before else rows[0])[1]

    marks = [("lift-off", at(lift_t))] if lift_t else []
    marks.append(("end", rows[-1][1]))
    print("  rotor  corner              " + "  ".join(f"{m:>9}" for m, _ in marks))
    effs = {m: effort(us, signs) for m, us in marks}
    for i in range(8):
        flag = "  <-- above 80 %" if effs["end"][i] > MAX_ROTOR_PCT else (
            "  <-- WEAK side" if effs["end"][i] < 0 else "")
        print(f"  {i + 1:>5}  {CORNER[i + 1]:<18}" + "  ".join(f"{effs[m][i]:8.0f}%" for m, _ in marks) + flag)
    for a, b in (("left", "right"), ("front", "back"), ("top", "bottom")):
        print(f"  {a:>6}/{b:<6} " + "  ".join(
            f"{side_mean(effs[m], a):5.0f}/{side_mean(effs[m], b):<5.0f}%" for m, _ in marks))
    e = effs["end"]
    L, R = side_mean(e, "left"), side_mean(e, "right")
    imb = abs(L - R) / max(1e-9, (L + R) / 2)
    worst = max(range(8), key=lambda i: e[i])
    ok_rotor = e[worst] <= MAX_ROTOR_PCT
    ok_lr = imb <= MAX_LR_IMBALANCE
    print(f"  check: highest rotor {worst + 1} at {e[worst]:.0f} % -> {'PASS' if ok_rotor else 'FAIL'} (<= {MAX_ROTOR_PCT:.0f} %)")
    print(f"  check: left/right imbalance {100 * imb:.0f} % -> {'PASS' if ok_lr else 'FAIL'} (<= {100 * MAX_LR_IMBALANCE:.0f} %)")
    return lift_t


def save_png(stamp, n, sp, moc, signs, t_start, lift_t):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    t0, rows = sp["t0"], sp["rows"]
    seg = [r for r in moc if t0 - 0.5 <= num(r["time_s"]) <= rows[-1][0] + 0.3 and r["valid"] == "1"]
    base = [r for r in moc if t0 - 2.0 <= num(r["time_s"]) <= t0 - 0.5 and r["valid"] == "1"]
    g = sum(-num(r["d_m"]) for r in base) / len(base) if base else 0.0
    fig, ax = plt.subplots(3, 1, figsize=(9, 8), sharex=True)
    tm = [num(r["time_s"]) - t0 for r in seg]
    ax[0].plot(tm, [math.degrees(num(r["roll_rad"])) for r in seg], label="roll", color="#2a6fdb")
    ax[0].plot(tm, [math.degrees(num(r["pitch_rad"])) for r in seg], label="pitch", color="#9a9a9a")
    ax[0].axhline(-30, ls="--", lw=0.8, color="#777")
    ax[0].axhline(30, ls="--", lw=0.8, color="#777")
    ax[0].set_ylabel("deg")
    ax[0].legend(loc="lower left")
    to = [r[0] - t0 for r in rows]
    for i in range(8):
        ax[1].plot(to, [effort(r[1], signs)[i] for r in rows], label=f"{i + 1}",
                   lw=2 if (i + 1) in FACES["left"] else 1, ls="-" if (i + 1) in FACES["left"] else ":")
    ax[1].axhline(100, ls="--", lw=0.8, color="#777")
    ax[1].axhline(MAX_ROTOR_PCT, ls=":", lw=0.8, color="#777")
    ax[1].set_ylabel("% on hover side")
    ax[1].legend(ncol=4, fontsize=8, loc="upper left", title="rotor (solid = left side)", title_fontsize=8)
    ax[2].plot(tm, [100 * (-num(r["d_m"]) - g) for r in seg], color="#555")
    ax[2].set_ylabel("height cm")
    ax[2].set_xlabel("s after the motors started")
    for a in ax:
        if lift_t:
            a.axvline(lift_t - t0, ls="--", lw=0.8, color="#2a6fdb")
        a.grid(alpha=0.3)
    fig.suptitle(f"Session {stamp}, motor-on attempt {n}")
    out = HERE / "reports" / f"flight_{stamp}_{n}.png"
    out.parent.mkdir(exist_ok=True)
    fig.tight_layout()
    fig.savefig(out, dpi=110)
    plt.close(fig)
    print(f"  plot: {out}")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("session", nargs="?", help="timestamp like 20261104_190320 (default: newest)")
    p.add_argument("--png", action="store_true", help="also save a plot per attempt in reports/")
    a = p.parse_args()
    stamps = sorted(f.stem[len("telemetry_"):] for f in LOGS.glob("telemetry_*.csv"))
    if not stamps:
        sys.exit(f"No telemetry_*.csv in {LOGS}")
    stamp = a.session or stamps[-1]
    if stamp not in stamps:
        sys.exit(f"Session {stamp} not found. Sessions: {', '.join(stamps)}")
    tele, moc = load(stamp)
    signs = hover_signs()
    t_start = num(tele[0]["time_s"])
    print(f"Session {stamp}: {len(tele)} telemetry rows, {len(moc)} OptiTrack rows, "
          f"{num(tele[-1]['time_s']) - t_start:.0f} s")
    print("Events:")
    for r in tele:
        if r["event"]:
            print(f"  {num(r['time_s']) - t_start:7.2f} s  {r['event']}")
    sps = spans(tele)
    if not sps:
        print("\nThe motors never left 1500 us in this session.")
        return
    for n, sp in enumerate(sps, 1):
        lift_t = report_span(n, sp, moc, signs, t_start)
        if a.png:
            save_png(stamp, n, sp, moc, signs, t_start, lift_t)


if __name__ == "__main__":
    main()
