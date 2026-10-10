# Lab 7 — Next Instruction Address Generation I

**Runs:** Mon 10/19 · Tue 10/20 · 3:45–5:45 PM, ECIII 237
**Status:** complete and simulation-verified. Slide deck written as content, not built as `.pptx`.

---

## What is here

| Path | Audience | Purpose |
|---|---|---|
| `handout/Lab7_spec.pdf` | **students** | Specification, 4 pages |
| `handout/Lab7_prelab.pdf` | **students** | Pre-lab, 2 pages, due 3:45 |
| `Lab7_student_files.zip` | **students** | Everything they open in Quartus |
| `examples/exe_1` | students | `pc_counter` — the PC at 8 bits, readable in a waveform |
| `examples/exe_2` | students | `branch_target` — the real `BLEZ` from the Lab 12 program |
| `examples/exe_3` | students | `addressing_traps` — **the two wrong versions, side by side** |
| `assignment/` | **students** | Flat project: `NIAG_NSA`, `NIAG_Rel`, `NIAG_Reg`, testbench |
| `slides/Lab7_slides.md` | you | 9 slides + what to say |
| `solution/` | **TA only** | Reference + 20-check testbench. **Never publish.** |
| `overleaf/lab07.tex` | students | Report chapter |
| `rubric.md`, `TA_notes.md` | you | Grading, the whiteboard moment, friction table |

---

## Simulation-verified

| What | Expected | Actual |
|---|---|---|
| exe_1 `pc_counter` | reset vector, sequential, jump, stall, async reset | ✅ `PASS`, 0 errors |
| exe_2 `branch_target` | real + boundary targets, forward and backward | ✅ `PASS`, 0 errors |
| exe_3 `addressing_traps` | **exactly 2** deliberate failures, values as documented | ✅ 2 errors, both intended |
| `assignment/` as shipped | compiles clean, fails on the first vector | ✅ as designed |
| `solution/` | all pass | ✅ `PASS — all 20 checks passed`, 0 errors |
| Overleaf template with `lab07` | builds | ✅ 39 pages, 0 warnings |

---

## The pedagogical spine

**One idea:** the PC is a register; everything else is address arithmetic. A counter
only counts — a program counter must jump, so "advance to the next instruction" is
just loading PC+4. Next week that single input becomes a five-way multiplexer and
sequential execution becomes one of its inputs.

**The whiteboard moment.** Slide 4's arithmetic is worked *with the room*, not shown
finished:

```
0x0C   0x18200002   BLEZ r1, +2
  NSA = 0x0C + 4 = 0x10 · offset = 2×4 = 0x08 · target = 0x18
```

That is instruction four of the program their CPU runs in Lab 12, and `0x18` is the
store that ends the loop. The "this is real, and you will run it" connection is what
makes the lab land.

**Two shapes of addressing bug**, named explicitly because they generalise:

| error | shape | tell-tale |
|---|---|---|
| forgot `<< 2` | off by a **factor** | target not a multiple of 4 |
| used PC not PC+4 | off by a **constant** 4 | still aligned, still nearly right |

Example 3 builds all three versions and two of its asserts fail on purpose, with the
values printed so students can compare the symptoms.

**Hand-compute before you simulate.** The first lab where students can genuinely
predict the hardware in advance, and the habit Lab 12 depends on entirely. Check-off
question 1 is a whiteboard derivation, not a waveform reading.

**Reuse is now structural.** `NIAG_Rel` takes an *already-extended* offset because
in the real CPU `ImmedXtnd` is a shared block feeding both the ALU and the branch
adder. The testbench wires the four components exactly as Lab 12 does. Step 1 of the
assignment is copying their own Lab 4 extender in.

---

## Canvas module

```
Module: Lab 7 — Next Instruction Address Generation I
  ├── Lab7_spec.pdf
  ├── Lab7_prelab.pdf              → due at 3:45
  ├── Lab7_student_files.zip
  ├── Lab 7 slides (PDF)           ← pending deck build
  ├── Reading: COD Ch. 2.7 and 4.3 (branch addressing, datapath)
  └── Reference: Lab 4 ImmedXtnd.vhd, Lab 2 RegN.vhd
        (publish after each lab's late deadline)
```

Do **not** publish `solution/`, `rubric.md`, or `TA_notes.md`.
