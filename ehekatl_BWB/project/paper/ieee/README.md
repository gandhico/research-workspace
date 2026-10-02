# IEEE manuscript build

The IEEEtran source is `ehekatl_lqr_deepc_ieee.tex`. It imports the generated
PDF figures from `../generated/`.

Regenerate evidence-backed tables and figures first:

```bash
cd /home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12
backstepping/ehekatl_xplane12_backstepping_bridge/.venv/bin/python -B \
  paper/generate_paper_results.py
```

Then build from this directory on a TeX installation containing IEEEtran,
`siunitx`, `booktabs`, `amsmath`, `graphicx`, `hyperref`, and `url`:

```bash
cd /home/ubuntu/GHYN/Xplane_controllers/EHEKATL_BWB_XP12/paper/ieee
pdflatex ehekatl_lqr_deepc_ieee.tex
pdflatex ehekatl_lqr_deepc_ieee.tex
```

Replace the placeholder author block before submission. The current execution
environment does not include a LaTeX engine, so the PDF must be compiled in a
TeX Live/MiKTeX installation or Overleaf.
