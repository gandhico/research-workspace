# Lab 8 — Next Instruction Address Generation II

**Runs:** Mon 10/26 · Tue 10/27 · 3:45–5:45 PM, ECIII 237
**Status:** complete and simulation-verified. Slide deck written as content, not built as `.pptx`.

---

## What is here

| Path | Audience | Purpose |
|---|---|---|
| `handout/Lab8_spec.pdf` | **students** | Specification, 4 pages |
| `handout/Lab8_prelab.pdf` | **students** | Pre-lab, 2 pages, due 3:45 |
| `Lab8_student_files.zip` | **students** | Everything they open in Quartus |
| `examples/exe_1` | students | `absolute_target` — the real `J`, and the 256 MB limit |
| `examples/exe_2` | students | `branch_conditions` — all 28 cases + complement-pair check |
| `examples/exe_3` | students | `pc_select` — **the same Sel code with Taken high and low** |
| `assignment/` | **students** | Flat project: `NIAG_Abslt`, `NIAG_Cond`, `NIAG_MUX`, `NIAG` |
| `slides/Lab8_slides.md` | you | 9 slides + what to say |
| `solution/` | **TA only** | Reference + 24-check testbench. **Never publish.** |
| `overleaf/lab08.tex` | students | Report chapter |
| `rubric.md`, `TA_notes.md` | you | Grading, the GTZ hunt, friction table |

---

## Simulation-verified

| What | Expected | Actual |
|---|---|---|
| exe_1 `absolute_target` | real `J`, boundaries, region confinement | ✅ `PASS`, 0 errors |
| exe_2 `branch_conditions` | 28 cases + both complement pairs | ✅ `PASS`, 0 errors |
| exe_3 `pc_select` | only the relative path is conditional | ✅ `PASS`, 0 errors |
| `assignment/` as shipped | compiles clean, fails on the first vector | ✅ as designed |
| `solution/` | all pass | ✅ `PASS — all 24 checks passed`, 0 errors |
| Overleaf template with `lab08` | builds | ✅ 45 pages, 0 warnings |

---

## A VHDL trap I hit while writing this

Example 2's complement-pair loop originally used an anonymous `declare … begin …
end;` block inside a process to scope its loop variables. **That is Ada, not VHDL** —
VHDL has no anonymous declarative block in sequential code. The variables now live in
the process declarative part, with a comment saying why. Worth knowing, because a
student who has written Ada will try it.

---

## The pedagogical spine

**One idea:** branch conditions are Boolean equations over the ALU flags. Two bits
from Lab 5 — `Zero` and `Neg` — and out of them comes every conditional branch the
machine has, in six one-line equations. The complement pairs (`GTZ`/`LEZ`,
`GEZ`/`LTZ`, `EQ`/`NEQ`) show the hardware is *smaller* than the instruction list,
which is the same lesson they meet at full scale in Labs 10–11.

**The error to hunt: `GTZ`.** It is not-negative **and** not-zero, not just
not-negative — that is `GEZ`. It passes every test where the result is non-zero,
which is most casual vectors. Check-off asks specifically for `GTZ` with `Zero` high.

**Two decisions, not one.** `Sel` says *which* address; `Cond` says *whether* a
relative branch is used. Only the relative path is conditional. A student who gates
`ABS` and `REG` with `Taken` builds a CPU that cannot jump whenever the last ALU
result was positive — intermittent by data, and horrible to find in Lab 12.

**This is the Lab 12 rehearsal.** Six components, no new logic. The three habits —
named association always, one signal per inter-component wire, read the wiring back
against the diagram once — all transfer directly to the twelve-component
integration.

**Example → assignment linkage.** exe_1's concatenation → `NIAG_Abslt`. exe_2's
seven rows → `NIAG_Cond`. exe_3's two-stage mux → `NIAG_MUX`. The top-level `NIAG`
then wires all three plus the three Lab 7 components.

---

## Canvas module

```
Module: Lab 8 — Next Instruction Address Generation II
  ├── Lab8_spec.pdf
  ├── Lab8_prelab.pdf              → due at 3:45
  ├── Lab8_student_files.zip
  ├── Lab 8 slides (PDF)           ← pending deck build
  ├── Reading: COD Ch. 2.8–2.10 (jumps, procedures, addressing modes)
  └── Reference: Lab 7 NIAG_NSA / NIAG_Rel / NIAG_Reg, Lab 4 ImmedXtnd
        (publish after each lab's late deadline)
```

Do **not** publish `solution/`, `rubric.md`, or `TA_notes.md`.
