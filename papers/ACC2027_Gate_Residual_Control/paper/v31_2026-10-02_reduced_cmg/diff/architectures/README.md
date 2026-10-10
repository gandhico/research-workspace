# Architecture figures

Ten diagrams of the architectures used in this research, in two
interchangeable formats. The TikZ files are the publication artefact; the
draw.io file is the editable one. They are kept one-for-one in sync.

| ID  | Diagram | TikZ | draw.io page |
|-----|---------|------|--------------|
| A1  | Main CMG–PES loop, single-column compact | `archA1.tex` | A1 |
| A2  | Main CMG–PES loop, two-column detailed (equations in blocks) | `archA2.tex` | A2 |
| A2p | A2 without the annotation note — **used as Fig. 1 in the paper** | `archA2p.tex` | (A2) |
| A3  | Three separable mechanisms (χ / η / β), layered view | `archA3.tex` | A3 |
| B1  | CMG unit internals, block form | `archB1.tex` | B1 |
| B1c | Column-native CMG coupling topology — **used as Fig. 3 in the paper** | `archB1c.tex` | (B1) |
| B2  | Antagonistic ± pair and why `W₀ = [I, −I]` | `archB2.tex` | B2 |
| C1  | Matched twin-plant evaluation harness | `archC1.tex` | C1 |
| D1  | Nengo realization: what is an `Ensemble`, what is a `Node` | `archD1.tex` | D1 |
| E1  | 3DOF Hover hardware loop (200 Hz / 2 kHz nesting, safety layer) | `archE1.tex` | E1 |
| F1  | 6-DOF cascade (outer position → inner attitude → allocator) | `archF1.tex` | F1 |
| G1  | Instantaneous PES vs annealed activity trace | `archG1.tex` | G1 |

Three proposals exist for the main architecture (A1 compact, A2 detailed,
A3 mechanism-separation) and two for the neuron (B1 block form, B2 the
antagonistic pair), so you can pick per figure slot.

## Rendered previews

* `architectures_deck.pdf` — all ten TikZ diagrams, one per page.
* `architectures_drawio.pdf` — the same ten, exported from draw.io.

## Using one in the paper

The preamble already carries what is needed:

```latex
\usepackage{tikz}
\usetikzlibrary{arrows.meta,positioning,fit,backgrounds,calc}
\input{figures/arch/arch_style.tex}
```

Then, in the body:

```latex
\begin{figure}[t]\centering
  \resizebox{0.95\columnwidth}{!}{\input{figures/arch/archB1c.tex}}
  \caption{...}\label{fig:...}
\end{figure}
```

Use `figure*` and `\resizebox{\textwidth}` for the wide ones (A2, A3, C1,
D1, F1, G1). The diagrams call `\eqref` with this paper's equation labels,
so the numbers track the text automatically.

## Editing

* **draw.io**: open `architectures.drawio` in the desktop app or at
  diagrams.net. Each architecture is a separate page.
* **regenerating the draw.io file**: `python make_drawio.py` rebuilds it
  from a compact node/edge spec. Edit the spec, not the XML, if you want
  the two formats to stay in sync.
* **previewing the TikZ set**: `pdflatex preview.tex` renders all ten with
  their explanatory notes. `preview_paper.tex` renders the two paper
  variants at their intended sizes.

The `note` blocks visible in the standalone previews are deliberately
absent from the paper variants (`archA2p`, `archB1c`) — that material
belongs in the caption at publication size.

## Style

`arch_style.tex` defines the shared look and is grayscale-safe for print:

| Style | Meaning |
|-------|---------|
| light fill (`clas`) | fixed classical component — never adapted |
| heavy border, mid fill (`neuro`) | neuromorphic / adapted component |
| dark fill (`plant`) | plant or hardware |
| dashed (`meas`) | computed from measurements, not a physical subsystem |
| dashed rounded box (`grp`) | grouping only |
