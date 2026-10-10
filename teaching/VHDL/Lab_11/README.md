# Lab 11 — Instruction Decoder II

**Runs:** Mon 11/16 · Tue 11/17 · 3:45–5:45 PM, ECIII 237
**Status:** complete and simulation-verified. Slide deck written as content, not built as `.pptx`.

---

## What is here

| Path | Audience | Purpose |
|---|---|---|
| `handout/Lab11_spec.pdf` | **students** | Specification, 4 pages |
| `handout/Lab11_prelab.pdf` | **students** | Pre-lab, 2 pages, due 3:45 |
| `Lab11_student_files.zip` | **students** | Everything they open in Quartus |
| `examples/exe_1` | students | `decode_lw_sw` — the shared adder, and the two signals that matter |
| `examples/exe_2` | students | `dontcare` — **two correct answers, proved** |
| `examples/exe_3` | students | `decode_flow` — BLEZ and J, and how sparse a row is |
| `assignment/` | **students** | `CPU_Pkg.vhd` (given), `Decoder.vhd`, table-driven testbench |
| `slides/Lab11_slides.md` | you | 8 slides + what to say |
| `solution/` | **TA only** | Complete decoder + table-driven testbench. **Never publish.** |
| `overleaf/lab11.tex` | students | Report chapter — **the complete control table lives here** |
| `rubric.md`, `TA_notes.md` | you | Grading, the SW/BLEZ hunts, friction table |

---

## Simulation-verified

| What | Expected | Actual |
|---|---|---|
| exe_1 `decode_lw_sw` | shared adder; SW's `RF_strb`/`RF_oe` | ✅ `PASS` 16/16, 0 errors |
| exe_2 `dontcare` | two implementations agree where it matters | ✅ `PASS`; differ on exactly ADD, SLL, J |
| exe_3 `decode_flow` | BLEZ scaling, J sparsity | ✅ `PASS` 14/14, 0 errors |
| `assignment/` as shipped | compiles clean, fails legibly (19 checks) | ✅ as designed |
| `solution/` | 8 instructions × 14 fields + safety + latch tests | ✅ `PASS — complete decoder, all 8 instructions verified` |
| Overleaf template with `lab11` | builds | ✅ 58 pages, **0 errors**, 0 warnings |

---

## A real bug found and fixed this round

The Overleaf template had been building with **97 LaTeX errors** that I had not
noticed, because I was only counting *warnings*. Cause: `lab07.tex` and `lab10.tex`
were written via shell heredoc, which collapsed every `\\` table-row separator to a
single `\`. Both files are now rewritten and the template builds with **0 errors**.

Lesson applied for the rest of the build: **all `.tex` goes through the Write tool,
never a heredoc**, and the template build now checks `^!` lines, not just warnings.

A second, smaller one: the shipped Lab 11 testbench table originally produced **117
failures** on first run — a wall of noise. It now ships with a single row (using
`0 =>`, because a one-element array aggregate is ambiguous in VHDL) and fails with
19 legible checks.

---

## The pedagogical spine

**One idea:** memory access and control flow are just four more rows.

**Three traps, all silent:**

| Trap | Symptom in Lab 12 |
|---|---|
| `SW` with `RF_strb = STROBE` | every store also corrupts a register; the program fails somewhere else entirely |
| `SW` with `RF_oe = HiZ` | the store writes `'Z'`, which the RAM happily stores |
| `BLEZ` without `IR_Xlsft = TWO` | every branch lands a quarter of the way to its target |

The third is Lab 7's "off by a factor" arriving through the decoder instead of the
adder — worth naming that connection out loud.

**Three observations once the table is complete**, all required in the report:
`ALU_Asel = IMMED` for four unrelated-looking instructions *because the adder is
shared*; `DM_rw` decided by one instruction out of eight, and `J` changing two
signals out of sixteen, *because control tables are sparse*; and `RF_strb` STROBE for
exactly the five instructions that produce a value worth keeping.

**Don't cares, and two correct answers.** Example 2 builds two implementations of
`IR_Xsel` that disagree on exactly ADD, SLL and J — the three that never read the
extender — and proves both correct. This is minimisation in a real control unit: the
same operation as a K-map in Lab 3, except the don't cares now come from the
*architecture*. The corollary is the more useful half: **over-specifying a test is
its own kind of bug.**

**Table-driven testing.** The expectation for each instruction lives in an array and
one loop checks 8 × 14 fields. Written from the *specification*, not from the
decoder — a test copied from the implementation agrees with the bug.

---

## Say this at Close, and mean it

> *Print your completed control table and bring it next week. Step three of the Lab
> 12 debugging method is: do the control signals match the table for this opcode?
> Without it you cannot do step three, and you will lose the session.*

---

## Canvas module

```
Module: Lab 11 — Instruction Decoder II
  ├── Lab11_spec.pdf
  ├── Lab11_prelab.pdf             → due at 3:45
  ├── Lab11_student_files.zip
  ├── Lab 11 slides (PDF)          ← pending deck build
  ├── Reading: COD Ch. 4.4 (control implementation, continued)
  └── Reference: Lab 10 Decoder.vhd (publish after Lab 10's late deadline)
```

Do **not** publish `solution/`, `rubric.md`, or `TA_notes.md`.
