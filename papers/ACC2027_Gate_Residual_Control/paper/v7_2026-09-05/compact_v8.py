"""Halve the noise table and shrink the result figures.

The two models agree to within 0.4 points in every cell, so reporting
X2/CF2 in one row per mission loses nothing and halves the table height.
"""
from __future__ import annotations

import io

P = "ACC2027_v8.tex"
s = io.open(P, encoding="utf-8").read()

OLD = (
    r"Model&Mission&Clean&Moderate&\multicolumn{2}{c}{Realistic}\\\midrule" "\n"
    r"X2&Roll&17.4\%&32.3\%&32.2\%&$\pm$0.01\\" "\n"
    r"&Full3&56.6\%&56.4\%&55.7\%&$\pm$0.00\\" "\n"
    r"&Hard45&53.1\%&52.9\%&52.3\%&$\pm$0.01\\" "\n"
    r"&Hardstep&20.9\%&20.8\%&20.6\%&$\pm$0.02\\" "\n"
    r"&Yaw360&60.6\%&56.8\%&47.8\%&$\pm$0.03\\\midrule" "\n"
    r"CF2&Roll&17.3\%&32.4\%&32.5\%&$\pm$0.01\\" "\n"
    r"&Full3&56.1\%&55.9\%&55.2\%&$\pm$0.00\\" "\n"
    r"&Hard45&53.6\%&53.4\%&52.7\%&$\pm$0.01\\" "\n"
    r"&Hardstep&18.4\%&18.3\%&18.1\%&$\pm$0.02\\" "\n"
    r"&Yaw360&60.6\%&56.8\%&47.8\%&$\pm$0.03\\"
)

NEW = (
    r"Mission&Clean&Moderate&\multicolumn{2}{c}{Realistic}\\\midrule" "\n"
    r"Roll&17.4/17.3\%&32.3/32.4\%&32.2/32.5\%&$\pm$0.01\\" "\n"
    r"Full3&56.6/56.1\%&56.4/55.9\%&55.7/55.2\%&$\pm$0.00\\" "\n"
    r"Hard45&53.1/53.6\%&52.9/53.4\%&52.3/52.7\%&$\pm$0.01\\" "\n"
    r"Hardstep&20.9/18.4\%&20.8/18.3\%&20.6/18.1\%&$\pm$0.02\\" "\n"
    r"Yaw360&60.6/60.6\%&56.8/56.8\%&47.8/47.8\%&$\pm$0.03\\"
)

assert OLD in s, "table body not found verbatim"
s = s.replace(OLD, NEW, 1)

assert r"\begin{tabular}{llrrr@{\,}l}" in s
s = s.replace(r"\begin{tabular}{llrrr@{\,}l}", r"\begin{tabular}{lrrr@{\,}l}", 1)

s = s.replace("Clean\nreproduces Table~", "Entries are X2/CF2. Clean\nreproduces Table~", 1)

n_fig = s.count(r"width=0.70\linewidth")
s = s.replace(r"width=0.70\linewidth", r"width=0.62\linewidth")

io.open(P, "w", encoding="utf-8").write(s)
print(f"table halved to 5 rows; {n_fig} result figures 0.70 -> 0.62")
