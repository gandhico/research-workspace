"""Select PES step size on validation phases, then report untouched test phase."""
import csv
import math
import sys
from collections import defaultdict
from pathlib import Path

base = Path(__file__).resolve().parent / "results"
source = base / "acc_multisignal_pes_2026-10-06.csv"
dest = base / "acc_multisignal_pes_selected_2026-10-06.csv"
if len(sys.argv) >= 2:
    source = Path(sys.argv[1])
if len(sys.argv) >= 3:
    dest = Path(sys.argv[2])
groups = defaultdict(list)
for row in csv.DictReader(source.open(encoding="utf-8-sig")):
    groups[(row["gamma"], row["readout"])].append(row)


def pair_rms(row, prefix):
    a = float(row[f"{prefix}_cold_rmse"])
    b = float(row[f"{prefix}_settled_rmse"])
    return math.hypot(a, b) / math.sqrt(2)


with dest.open("w", newline="", encoding="utf-8") as handle:
    writer = csv.writer(handle)
    writer.writerow(("gamma", "readout", "selected_eta", "validation_pair_rmse",
                     "test_pair_rmse", "test_cold_rmse", "test_settled_rmse",
                     "late_online_train_rmse"))
    for (gamma, readout), rows in sorted(groups.items()):
        selected = min(rows, key=lambda row: pair_rms(row, "validation"))
        writer.writerow((gamma, readout, selected["eta"],
                         f"{pair_rms(selected, 'validation'):.9g}",
                         f"{pair_rms(selected, 'test'):.9g}",
                         selected["test_cold_rmse"],
                         selected["test_settled_rmse"],
                         selected["late_online_train_rmse"]))
print(f"{len(groups)} validation-selected rows -> {dest}")
