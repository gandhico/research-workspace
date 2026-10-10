# Lab 2 — Master–Slave Flip-Flop and the N-Bit Register

**Runs:** Mon 9/14 · Tue 9/15 · 3:45–5:45 PM, ECIII 237
**Status:** complete and simulation-verified. Slide deck is written as content, not built as `.pptx`.

---

## What is here

| Path | Audience | Purpose |
|---|---|---|
| `handout/Lab2_spec.pdf` | **students** | Assignment specification, 4 pages |
| `handout/Lab2_prelab.pdf` | **students** | Pre-lab, 3 questions, due 3:45 |
| `Lab2_student_files.zip` | **students** | Everything they open in Quartus |
| `examples/exe_1` | students | `ms_flipflop` — structural, from two latches |
| `examples/exe_2` | students | `dff` — behavioural, asserted identical to exe_1 |
| `examples/exe_3` | students | `reg_n` — one entity, two widths |
| `assignment/` | **students** | Flat Quartus project |
| `slides/Lab2_slides.md` | you | 11 slides + what to say |
| `solution/` | **TA only** | Reference + 20-check testbench. **Never publish.** |
| `overleaf/lab02.tex` | students | Report chapter (also in the template) |
| `rubric.md`, `TA_notes.md` | you | Grading, and the measured diagnostic table |

---

## Simulation-verified

| What | Expected | Actual |
|---|---|---|
| exe_1 `ms_flipflop` | edge behaviour holds | ✅ `PASS`, 0 errors |
| exe_2 structural vs behavioural | the two agree on every vector | ✅ `PASS — behaviourally identical`, 0 errors |
| exe_3 `reg_n` at 4 and 12 bits | one entity serves both | ✅ `PASS — both widths correct`, 0 errors |
| `assignment/` as shipped | compiles, runs, reports failures | ✅ compiles clean, fails as designed |
| `solution/` | all pass | ✅ `PASS — all 20 checks passed`, 0 errors |
| Overleaf template with `lab02` | builds | ✅ 13 pages, 0 warnings |

**The measured diagnostic** (in `TA_notes.md`): a correct `RegN` body left with the
supplied incomplete `process (Clk)` fails **exactly the two async-reset checks** and
passes everything else. That precise signature is the debugging lesson — which
checks fail names the missing signal.

---

## Three deliberate design choices

**1. `TransLatch.vhd` in the assignment folder is the empty Lab 1 skeleton.**
Step 1 of the assignment is to overwrite it with their own Lab 1 solution. This
keeps the project compiling out of the box, leaks no Lab 1 answer, and starts the
habit that Lab 12 depends on. **Anyone whose Lab 1 latch never worked needs the
reference version at 3:45**, not at 5:00 — Lab 2 is blocked without it.

**2. `RegN`'s sensitivity list ships incomplete, and the rule has changed.**
Lab 1's rule (every signal the process reads) is wrong for a clocked process. The
correct list is the clock plus asynchronous controls only. Students must work that
out and justify it in the report; it is a graded question.

**3. Top-level entity is `RegN`, not the flip-flop.** The Fitter then reports the
register count for a 32-bit register, which must be 32. This is the first week E4
carries diagnostic weight, and it sets up Lab 6, where the count must be ~1024.

---

## Changes this fed back into the program plan

Building Lab 2 surfaced three things now reconciled in `_planning/design/01_Lab_Program.md`:

- **`MSFlipFlop` gained a `Clr` port** wired to *both* latches. The plan had it as
  `D, Clk → Q`. Clearing only the slave lets the master push the stale value back at
  the next edge — a good bug to demonstrate, and worth the extra port.
- **`RegDemo` dropped.** The testbench instantiates `RegN` at widths 5 and 32, which
  proves the generic without a third file.
- **`RegN`'s VHDL idiom corrected.** The plan showed `elsif rising_edge(Clk) and
  Ld='1'`. That simulates fine but is not the idiom synthesisers expect; it is now
  the nested `if`, and the spec explains why.

---

## Canvas module

```
Module: Lab 2 — Master–Slave Flip-Flop and the N-Bit Register
  ├── Lab2_spec.pdf
  ├── Lab2_prelab.pdf              → due at 3:45
  ├── Lab2_student_files.zip
  ├── Lab 2 slides (PDF)           ← pending deck build
  ├── Reading: H&H Ch. 3.2–3.3; COD App. B (sequential elements)
  └── Reference: Lab 1 TransLatch.vhd  (publish after Lab 1's late deadline)
```

Do **not** publish `solution/`, `rubric.md`, or `TA_notes.md`.
