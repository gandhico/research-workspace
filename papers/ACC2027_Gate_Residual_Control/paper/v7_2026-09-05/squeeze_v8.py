"""Non-destructive squeeze: shrink float sizes and tighten table spacing.

No figure or table is removed and no result is dropped; only sizes change.
"""
from __future__ import annotations

import io

P = "ACC2027_v8.tex"
s = io.open(P, encoding="utf-8").read()
log = []


def swap(old: str, new: str, tag: str, required: bool = True) -> None:
    global s
    if old not in s:
        if required:
            raise SystemExit(f"FAILED [{tag}]")
        return
    s = s.replace(old, new, 1)
    log.append(tag)


# nomenclature: tighter rows
swap(r"\renewcommand{\arraystretch}{0.92}",
     r"\renewcommand{\arraystretch}{0.84}", "nomenclature-rows")

# architecture figure: a touch narrower
swap(r"\resizebox{\textwidth}{!}{\input{figures/arch/archA2p.tex}}",
     r"\resizebox{0.93\textwidth}{!}{\input{figures/arch/archA2p.tex}}",
     "arch-figure")

# CMG unit figure
swap(r"\resizebox{0.95\columnwidth}{!}{\input{figures/arch/archB1c.tex}}",
     r"\resizebox{0.86\columnwidth}{!}{\input{figures/arch/archB1c.tex}}",
     "cmgunit-figure")

# hover figure
swap(r"\includegraphics[width=0.88\linewidth]{hover_intermittent}",
     r"\includegraphics[width=0.78\linewidth]{hover_intermittent}",
     "hover-figure")

# noise table
swap(r"\label{tab:noise}\centering\footnotesize",
     r"\label{tab:noise}\centering\scriptsize", "noise-table")

# vehicle photographs: they are decorative next to the architecture figure
swap(r"\begin{minipage}[b]{0.31\textwidth}", r"\begin{minipage}[b]{0.29\textwidth}",
     "vehicles-1")
swap(r"\begin{minipage}[b]{0.31\textwidth}", r"\begin{minipage}[b]{0.29\textwidth}",
     "vehicles-2")
swap(r"\begin{minipage}[b]{0.34\textwidth}", r"\begin{minipage}[b]{0.31\textwidth}",
     "vehicles-3")

io.open(P, "w", encoding="utf-8").write(s)
print("squeezed: " + ", ".join(log))
