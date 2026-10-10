# Lab 10 — Instruction Decoder I

**Runs:** Mon 11/9 · Tue 11/10 · 3:45–5:45 PM, ECIII 237
**Status:** complete and simulation-verified. Slide deck written as content, not built as `.pptx`.

---

## Say the scope first

The fear in this lab is scope, and the scope is small. Slide 2, before anything else:

> *This CPU has **eight** instructions — the ones its program uses. Four this week,
> four next week. The instruction set manual is not your specification; the control
> table is, and I am giving it to you filled in.*

Students who go looking for the full MIPS instruction list will drown, and they will
do it in the first ten minutes if you let them.

---

## The intellectual close of the course

Slide 3, and it deserves a pause:

> *In Lab 1 you took a four-row truth table and wrote one Boolean equation. Today
> you take an eight-row table and write sixteen. That is the entire difference.
> Nothing new has been introduced since week one — the control unit of a processor
> **is** a truth table. That is not an analogy.*

---

## What is here

| Path | Audience | Purpose |
|---|---|---|
| `handout/Lab10_spec.pdf` | **students** | Specification, 4 pages |
| `handout/Lab10_prelab.pdf` | **students** | Pre-lab, 2 pages, due 3:45 |
| `Lab10_student_files.zip` | **students** | Everything they open in Quartus |
| `examples/exe_1` | students | `fields` — all three formats, on real instructions |
| `examples/exe_2` | students | `decode_add` — one instruction end to end, the template |
| `examples/exe_3` | students | `latch_storm` — **two decoders, one line apart** |
| `assignment/` | **students** | `CPU_Pkg.vhd` (given), `Decoder.vhd`, testbench |
| `slides/Lab10_slides.md` | you | 8 slides + what to say |
| `solution/` | **TA only** | Reference + 26-check testbench. **Never publish.** |
| `overleaf/lab10.tex` | students | Report chapter |
| `rubric.md`, `TA_notes.md` | you | Grading, the latch hunt, friction table |

---

## Simulation-verified

| What | Expected | Actual |
|---|---|---|
| exe_1 `fields` | all fields on four real instructions | ✅ `PASS`, 0 errors |
| exe_2 `decode_add` | five signals set, eleven safe defaults | ✅ `PASS`, 0 errors |
| exe_3 `latch_storm` | **exactly one** deliberate failure | ✅ 1 error; `bad_decode` shows `'U'` then `'1'`, `good_decode` `'0'` both times |
| `assignment/` as shipped | compiles clean, fails on the first vector | ✅ as designed |
| `solution/` | all pass | ✅ `PASS — all 26 checks passed`, 0 errors |
| Overleaf template with `lab10` | builds | ✅ 54 pages, 0 warnings |

---

## The pedagogical spine

**One idea:** a control unit is one truth table with sixteen output columns.

**The record type is introduced here**, with a justification: sixteen separate ports
through every entity would guarantee a wiring error. In hardware nothing changes —
a record is sixteen wires either way — but at this size it is the difference between
a design you can debug and one you cannot.

**The default is a safety property, not a coding convention.** `CTRL_DEFAULT` gives
no register write, no memory access, no bus driving, PC advances. A decoder that
does something *arbitrary* with an instruction it does not recognise is a CPU that
corrupts memory when it hits bad data.

**The third appearance of one rule.** *No assignment means hold the previous value.*
Lab 1's missing `else` — wanted. Lab 3's missing `when others` — not wanted. Lab 10 —
sixteen at once, and the most dangerous of the three, because in Lab 12 the symptom
is *every instruction works alone, the program still fails, and it fails differently
depending on order.*

**The order-dependence test.** Required in the testbench, and it is the check a
single-instruction-at-a-time testbench can never make. Example 3 demonstrates it
directly: the same `LUI` decodes differently depending on whether an `ADDI` preceded
it.

**A question that sets up next week:** *why does `ADD` leave `IR_Xsel` alone?*
Because it never reads the extender, so the value is a **don't care** — which is
exactly the point Lab 11 develops into two different correct equations.

---

## Canvas module

```
Module: Lab 10 — Instruction Decoder I
  ├── Lab10_spec.pdf
  ├── Lab10_prelab.pdf             → due at 3:45; bring the format sheet
  ├── Lab10_student_files.zip
  ├── Lab 10 slides (PDF)          ← pending deck build
  └── Reading: COD Ch. 4.4 (a simple control implementation); H&H Ch. 7.3
```

Do **not** publish `solution/`, `rubric.md`, or `TA_notes.md`.
