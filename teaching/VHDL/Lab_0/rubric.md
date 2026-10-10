# Lab 0 — Grading Rubric
### 100 points · the standard course rubric, identical for every lab

| Component | Pts | Source |
|---|---|---|
| Pre-lab, submitted at the start of the session | 5 | your record |
| Design compiles cleanly, warnings explained | 25 | report evidence |
| Testbench and test vectors, coverage justified | 20 | report |
| Simulation results match the specification | 20 | report |
| Report chapter quality | 15 | report |
| In-lab demonstration and explanation | 15 | your check-off sheet |
| **Total** | **100** | |

Late work is accepted for one week at **−20 points**.

**85 points are readable from the report** (pre-lab + the four report components).
The remaining 15 (demonstration) come from the bench.

**Lab 0 pre-lab:** 5 points awarded to everyone.

---

## What each report component means in practice

**Compiles cleanly, warnings explained (25).** Evidence that the design was
actually built: Quartus Flow Summary or Messages window, 0 errors, and the warnings
sorted into *fix / explain / ignore*. The RTL Viewer belongs here too — it is the
check that the tool understood the design. A report with no Quartus output cannot
score well here even if the VHDL is perfect.

**Testbench and test vectors, coverage justified (20).** The testbench is
**self-checking** (`assert`, not eyeballing), the vectors are listed, and there is
a **coverage argument in words** — which wrong design each vector would catch.

**Simulation results match the specification (20).** A waveform per circuit, each
with a caption that says **what it proves**, plus the transcript or PASS line.

**Report chapter quality (15).** The seven sections; truth tables with **numbered
rows**; the three-line derivation with **the law named**; code included as text;
and a Discussion describing one real problem, how it was found and what it taught.

---

## Automatic deductions

| | |
|---|---|
| Figure with no interpreting sentence | −4 each (cap −12) |
| Template placeholder left in the PDF (`PASTE SCREENSHOT HERE`, `Insert value`, `Placeholder:`) | −10 |
| Code shown only as a screenshot instead of text | −5 |
| Testbench applies stimulus but checks nothing | −8 |
| "Everything worked first try" as the whole Discussion | −6 |
| Simplification law never named | −5 |
| Truth-table rows not numbered | −5 |
| Model chapter from the course template submitted unmodified | **report returned, no grade** — see note |

## Note on the model chapter

`Overleaf_template/labs/lab00.tex` ships as a **worked model chapter** (majority3)
so students can see the expected standard. A submission that is only that chapter,
unmodified, contains no student work. Treat it as a missing submission and ask for
a resubmission — it is usually a misunderstanding of what the template is for.
